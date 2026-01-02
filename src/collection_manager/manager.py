"""
Collection Manager - Safe Plex collection creation and management

Based on Kometa's safe collection patterns (MIT License)
Incorporates code from Kometa-Team/Kometa (modules/plex.py)
"""

import logging
from typing import List, Dict, Optional
from plexapi.server import PlexServer
from plexapi.library import LibrarySection
from plexapi.collection import Collection
from plexapi.exceptions import NotFound
from .tmdb_helper import TMDBHelper

logger = logging.getLogger(__name__)


class CollectionManager:
    """
    Safe collection manager for Plex

    Uses atomic operations and batch edits to safely manage collections
    without risking library corruption.
    """

    def __init__(self, plex_url: str, plex_token: str, library_name: str, dry_run: bool = False, tmdb_api_key: Optional[str] = None):
        """
        Initialize collection manager

        Args:
            plex_url: Plex server URL (e.g., 'http://192.168.1.20:32400')
            plex_token: Plex authentication token
            library_name: Library name (e.g., 'Movies')
            dry_run: If True, preview operations without applying changes
            tmdb_api_key: TMDB API key (required for keyword collections)
        """
        self.plex_url = plex_url
        self.plex_token = plex_token
        self.library_name = library_name
        self.dry_run = dry_run

        # Connect to Plex
        self.server = PlexServer(plex_url, plex_token)
        self.library = self.server.library.section(library_name)

        # Initialize TMDB helper if API key provided
        self.tmdb = TMDBHelper(tmdb_api_key) if tmdb_api_key else None

        logger.info(f"Connected to Plex: {self.server.friendlyName}")
        logger.info(f"Library: {library_name} ({len(self.library.all())} items)")

    def get_collection(self, title: str) -> Optional[Collection]:
        """
        Get collection by title

        Args:
            title: Collection title

        Returns:
            Collection object or None if not found
        """
        try:
            return self.library.collection(title)
        except NotFound:
            return None

    def create_collection(
        self,
        title: str,
        items: List,
        description: Optional[str] = None,
        sort_title: Optional[str] = None
    ) -> Optional[Collection]:
        """
        Create a new collection safely

        Based on Kometa's create_blank_collection and alter_collection methods.

        Args:
            title: Collection title
            items: List of Plex items to add
            description: Collection description (optional)
            sort_title: Sort title for ordering (optional)

        Returns:
            Created collection or None if dry-run
        """
        if self.dry_run:
            logger.info(f"[DRY-RUN] Would create collection: {title}")
            logger.info(f"[DRY-RUN] Would add {len(items)} items")
            return None

        # Check if collection already exists
        existing = self.get_collection(title)
        if existing:
            logger.warning(f"Collection '{title}' already exists. Use add_to_collection() instead.")
            return existing

        if not items:
            logger.warning(f"No items to add to collection '{title}'")
            return None

        try:
            # Create collection with first item
            # This is the safest approach - collection must have at least one item
            logger.info(f"Creating collection: {title}")
            collection = self.library.createCollection(
                title=title,
                items=[items[0]]
            )

            # Set description if provided
            if description:
                collection.editSummary(description)

            # Set sort title if provided
            if sort_title:
                collection.editSortTitle(sort_title)

            logger.info(f"✓ Created collection: {title}")

            # Add remaining items in batches (safer than all at once)
            if len(items) > 1:
                self.add_to_collection(collection, items[1:])

            return collection

        except Exception as e:
            logger.error(f"✗ Failed to create collection '{title}': {e}")
            return None

    def add_to_collection(
        self,
        collection: Collection,
        items: List,
        batch_size: int = 100
    ) -> int:
        """
        Add items to an existing collection in batches

        Based on Kometa's alter_collection batch editing approach.

        Args:
            collection: Collection object
            items: List of items to add
            batch_size: Number of items per batch (default 100)

        Returns:
            Number of items successfully added
        """
        if self.dry_run:
            logger.info(f"[DRY-RUN] Would add {len(items)} items to '{collection.title}'")
            return 0

        success_count = 0
        failed_count = 0

        # Process in batches for safety
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]

            try:
                # Use batchMultiEdits for atomic operation
                self.library.batchMultiEdits(batch)
                collection.addItems(batch)
                self.library.saveMultiEdits()

                success_count += len(batch)
                logger.info(f"✓ Added {len(batch)} items to '{collection.title}' ({success_count}/{len(items)})")

            except Exception as e:
                failed_count += len(batch)
                logger.error(f"✗ Failed to add batch {i//batch_size + 1}: {e}")
                # Continue with next batch - don't let one failure break everything

        logger.info(f"Collection '{collection.title}': {success_count} added, {failed_count} failed")
        return success_count

    def create_decade_collections(self, decades: List[Dict]) -> List[Collection]:
        """
        Create decade collections (e.g., 1980s, 1990s, 2000s)

        Args:
            decades: List of decade configs:
                [
                    {"title": "1980s Movies", "start": 1980, "end": 1989},
                    {"title": "1990s Movies", "start": 1990, "end": 1999}
                ]

        Returns:
            List of created collections
        """
        created_collections = []

        for decade in decades:
            title = decade['title']
            start_year = decade['start']
            end_year = decade['end']

            logger.info(f"\nProcessing decade: {title} ({start_year}-{end_year})")

            # Get all items and filter by year manually (PlexAPI year filters are broken)
            all_items = self.library.all()
            items = [
                item for item in all_items
                if hasattr(item, 'year') and item.year and start_year <= item.year <= end_year
            ]

            logger.info(f"  Found {len(items)} items in year range {start_year}-{end_year}")

            if not items:
                logger.warning(f"No items found for {title}")
                continue

            # Create collection
            collection = self.create_collection(
                title=title,
                items=items,
                description=f"Movies from {start_year} to {end_year}",
                sort_title=f"!Decade {start_year}s"  # ! prefix sorts collections first
            )

            if collection:
                created_collections.append(collection)

        return created_collections

    def create_studio_collections(self, studios: List[Dict]) -> List[Collection]:
        """
        Create studio collections (e.g., Marvel, DC, Disney)

        Args:
            studios: List of studio configs:
                [
                    {"title": "Marvel", "studios": ["Marvel Studios"]},
                    {"title": "DC", "studios": ["DC Comics", "Warner Bros."]}
                ]

        Returns:
            List of created collections
        """
        created_collections = []

        for studio_config in studios:
            title = studio_config['title']
            studio_names = studio_config['studios']

            logger.info(f"\nProcessing studio collection: {title}")

            # Search for items from any of the studios
            all_items = []
            for studio_name in studio_names:
                items = self.library.search(studio=studio_name)
                all_items.extend(items)
                logger.info(f"  Found {len(items)} items from '{studio_name}'")

            # Remove duplicates
            unique_items = list({item.ratingKey: item for item in all_items}.values())

            if not unique_items:
                logger.warning(f"No items found for {title}")
                continue

            # Create collection
            collection = self.create_collection(
                title=title,
                items=unique_items,
                description=f"Movies from {', '.join(studio_names)}",
                sort_title=f"!Studio {title}"
            )

            if collection:
                created_collections.append(collection)

        return created_collections

    def _match_tmdb_ids_to_plex(self, tmdb_ids: List[int]) -> List:
        """
        Match TMDB IDs to Plex items

        Args:
            tmdb_ids: List of TMDB movie IDs

        Returns:
            List of Plex items that match the TMDB IDs
        """
        matched_items = []
        all_items = self.library.all()

        for item in all_items:
            # Get item GUIDs (Plex stores TMDB IDs here)
            for guid in item.guids:
                if 'tmdb://' in guid.id:
                    # Extract TMDB ID from guid like "tmdb://12345"
                    item_tmdb_id = int(guid.id.split('tmdb://')[1])
                    if item_tmdb_id in tmdb_ids:
                        matched_items.append(item)
                        break

        return matched_items

    def create_keyword_collections(self, keyword_collections: List[Dict]) -> List[Collection]:
        """
        Create keyword-based collections using TMDB

        Args:
            keyword_collections: List of keyword configs:
                [
                    {"title": "Zombies", "keyword_id": 12377, "description": "Movies featuring the undead"},
                    {"title": "Time Travel", "keyword_id": 4379}
                ]

        Returns:
            List of created collections
        """
        if not self.tmdb:
            logger.error("TMDB API key not configured - cannot create keyword collections")
            return []

        created_collections = []

        for keyword_config in keyword_collections:
            title = keyword_config['title']
            keyword_id = keyword_config.get('keyword_id')
            collection_id = keyword_config.get('collection_id')
            description = keyword_config.get('description', '')
            sort_title = keyword_config.get('sort_title', f"!{title}")

            logger.info(f"\nProcessing keyword collection: {title}")

            # Fetch TMDB IDs
            if keyword_id:
                logger.info(f"  Fetching movies with keyword ID {keyword_id}...")
                tmdb_ids = self.tmdb.get_movies_by_keyword(keyword_id)
            elif collection_id:
                logger.info(f"  Fetching TMDB collection {collection_id}...")
                tmdb_ids = self.tmdb.get_movies_in_collection(collection_id)
            else:
                logger.warning(f"No keyword_id or collection_id specified for '{title}'")
                continue

            if not tmdb_ids:
                logger.warning(f"No TMDB movies found for {title}")
                continue

            logger.info(f"  Found {len(tmdb_ids)} movies on TMDB, matching to Plex...")

            # Match TMDB IDs to Plex items
            items = self._match_tmdb_ids_to_plex(tmdb_ids)

            if not items:
                logger.warning(f"No matching items found in Plex for {title}")
                continue

            logger.info(f"  Matched {len(items)} items in Plex library")

            # Create collection
            collection = self.create_collection(
                title=title,
                items=items,
                description=description,
                sort_title=sort_title
            )

            if collection:
                created_collections.append(collection)

        return created_collections

    def create_genre_collections(self, genre_collections: List[Dict]) -> List[Collection]:
        """
        Create collections based on multiple genre filters

        Args:
            genre_collections: List of genre configs:
                [
                    {"title": "True Crime", "genres": ["Crime", "Documentary"]},
                    {"title": "Horror Mystery", "genres": ["Horror", "Mystery"]}
                ]

        Returns:
            List of created collections
        """
        created_collections = []

        for genre_config in genre_collections:
            title = genre_config['title']
            genres = genre_config['genres']
            description = genre_config.get('description', '')
            sort_title = genre_config.get('sort_title', f"!{title}")

            logger.info(f"\nProcessing genre collection: {title}")
            logger.info(f"  Filtering by genres: {', '.join(genres)}")

            # Get all items and filter by all genres
            all_items = self.library.all()
            items = []

            for item in all_items:
                # Check if item has ALL required genres
                item_genres = [g.tag for g in item.genres] if hasattr(item, 'genres') else []
                if all(genre in item_genres for genre in genres):
                    items.append(item)

            if not items:
                logger.warning(f"No items found with genres {genres}")
                continue

            logger.info(f"  Found {len(items)} items matching all genres")

            # Create collection
            collection = self.create_collection(
                title=title,
                items=items,
                description=description or f"Movies with {' + '.join(genres)}",
                sort_title=sort_title
            )

            if collection:
                created_collections.append(collection)

        return created_collections

    def delete_collection(self, collection_title: str) -> bool:
        """
        Delete a collection (rollback mechanism)

        Args:
            collection_title: Collection title to delete

        Returns:
            True if deleted, False if not found or failed
        """
        if self.dry_run:
            logger.info(f"[DRY-RUN] Would delete collection: {collection_title}")
            return False

        collection = self.get_collection(collection_title)
        if not collection:
            logger.warning(f"Collection '{collection_title}' not found")
            return False

        try:
            collection.delete()
            logger.info(f"✓ Deleted collection: {collection_title}")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to delete collection '{collection_title}': {e}")
            return False

    def list_collections(self) -> List[str]:
        """
        List all collections in the library

        Returns:
            List of collection titles
        """
        collections = self.library.collections()
        return [c.title for c in collections]


def main():
    """Example usage"""
    import json
    import argparse

    # Parse arguments
    parser = argparse.ArgumentParser(description='Kometizarr Collection Manager')
    parser.add_argument('--config', default='config.json', help='Config file path')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without applying')
    args = parser.parse_args()

    # Load config
    with open(args.config) as f:
        config = json.load(f)

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Initialize manager
    manager = CollectionManager(
        plex_url=config['plex']['url'],
        plex_token=config['plex']['token'],
        library_name=config['plex']['library'],
        dry_run=args.dry_run or config['collections'].get('dry_run', False),
        tmdb_api_key=config['apis']['tmdb']['api_key']
    )

    # Create decade collections
    if config['collections']['decades']['enabled']:
        logger.info("\n" + "=" * 60)
        logger.info("Creating Decade Collections")
        logger.info("=" * 60)

        manager.create_decade_collections(
            config['collections']['decades']['ranges']
        )

    # Create studio collections
    if config['collections'].get('studios', {}).get('enabled'):
        logger.info("\n" + "=" * 60)
        logger.info("Creating Studio Collections")
        logger.info("=" * 60)

        manager.create_studio_collections(
            config['collections']['studios']['collections']
        )

    # Create keyword collections
    if config['collections'].get('keywords', {}).get('enabled'):
        logger.info("\n" + "=" * 60)
        logger.info("Creating Keyword Collections")
        logger.info("=" * 60)

        manager.create_keyword_collections(
            config['collections']['keywords']['collections']
        )

    # Create genre collections
    if config['collections'].get('genres', {}).get('enabled'):
        logger.info("\n" + "=" * 60)
        logger.info("Creating Genre Collections")
        logger.info("=" * 60)

        manager.create_genre_collections(
            config['collections']['genres']['collections']
        )

    logger.info("\n" + "=" * 60)
    logger.info("✅ Collection management complete!")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
