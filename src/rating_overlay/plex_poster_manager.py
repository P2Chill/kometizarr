"""
Plex Poster Manager - Apply rating overlays to Plex library

Integrates all components: backup, rating fetch, overlay, upload
MIT License - Copyright (c) 2026 Kometizarr Contributors
"""

import logging
import time
from pathlib import Path
from typing import Optional, Dict, List
from plexapi.server import PlexServer
from plexapi.library import LibrarySection

from .backup_manager import PosterBackupManager
from .rating_fetcher import RatingFetcher
from .badge_generator import BadgeGenerator
from .overlay_composer import OverlayComposer
from .multi_rating_badge import MultiRatingBadge
from ..utils.logger import ProgressTracker, print_header, print_subheader, print_summary

logger = logging.getLogger(__name__)


class PlexPosterManager:
    """Apply rating overlays to Plex posters with automatic backup"""

    def __init__(
        self,
        plex_url: str,
        plex_token: str,
        library_name: str,
        tmdb_api_key: str,
        omdb_api_key: Optional[str] = None,
        mdblist_api_key: Optional[str] = None,
        backup_dir: str = '/tmp/kometizarr_backups',
        badge_style: str = 'default',
        dry_run: bool = False
    ):
        """
        Initialize Plex poster manager

        Args:
            plex_url: Plex server URL
            plex_token: Plex authentication token
            library_name: Library name (e.g., 'Movies')
            tmdb_api_key: TMDB API key
            omdb_api_key: Optional OMDb API key
            backup_dir: Directory for poster backups
            badge_style: Badge style ('default', 'imdb', 'minimal', etc.)
            dry_run: If True, preview operations without applying
        """
        self.plex_url = plex_url
        self.plex_token = plex_token
        self.library_name = library_name
        self.dry_run = dry_run

        # Connect to Plex
        self.server = PlexServer(plex_url, plex_token)
        self.library = self.server.library.section(library_name)

        # Initialize components
        self.backup_manager = PosterBackupManager(backup_dir)
        self.rating_fetcher = RatingFetcher(tmdb_api_key, omdb_api_key, mdblist_api_key)
        self.badge_generator = BadgeGenerator(style=badge_style)
        self.overlay_composer = OverlayComposer(self.badge_generator)
        self.multi_rating_badge = MultiRatingBadge()  # New multi-source badge

        # Temp directory for processing
        self.temp_dir = Path('/tmp/kometizarr_temp')
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Connected to Plex: {self.server.friendlyName}")
        logger.info(f"Library: {library_name} ({len(self.library.all())} items)")
        if dry_run:
            logger.info("DRY-RUN MODE: No changes will be applied")

    def _extract_tmdb_id(self, guids: list) -> Optional[int]:
        """Extract TMDB ID from Plex GUIDs"""
        for guid in guids:
            if 'tmdb://' in guid.id:
                return int(guid.id.split('tmdb://')[1])
        return None

    def _extract_imdb_id(self, guids: list) -> Optional[str]:
        """Extract IMDb ID from Plex GUIDs"""
        for guid in guids:
            if 'imdb://' in guid.id:
                return guid.id.split('imdb://')[1]
        return None

    def _extract_plex_ratings(self, movie) -> Dict[str, float]:
        """
        Extract ratings from Plex's own metadata

        Plex stores ratings from multiple sources in the ratings array:
        - TMDB (audience, 0-10 scale)
        - IMDb (audience, 0-10 scale)
        - RT Critic (critic, 0-10 scale -> multiply by 10 for %)
        - RT Audience (audience, 0-10 scale -> multiply by 10 for %)

        Returns:
            Dict with available ratings: {'tmdb': 7.5, 'imdb': 6.8, 'rt_critic': 30.0, 'rt_audience': 92.0}
        """
        plex_ratings = {}

        if hasattr(movie, 'ratings'):
            for rating in movie.ratings:
                rating_type = rating.type
                rating_value = rating.value
                rating_image = rating.image if hasattr(rating, 'image') else ''

                # RT Critic (critic type with RT image)
                if rating_type == 'critic' and 'rottentomatoes' in rating_image:
                    plex_ratings['rt_critic'] = rating_value * 10  # Convert 0-10 to 0-100%

                # RT Audience (audience type with RT image)
                elif rating_type == 'audience' and 'rottentomatoes' in rating_image:
                    plex_ratings['rt_audience'] = rating_value * 10  # Convert 0-10 to 0-100%

                # IMDb (audience type with imdb image)
                elif rating_type == 'audience' and 'imdb' in rating_image:
                    plex_ratings['imdb'] = rating_value

                # TMDB (audience type with themoviedb image)
                elif rating_type == 'audience' and 'themoviedb' in rating_image:
                    plex_ratings['tmdb'] = rating_value

        return plex_ratings

    def process_movie(
        self,
        movie,
        position: str = 'northwest',
        force: bool = False
    ) -> bool:
        """
        Process a single movie: backup, overlay, upload

        Args:
            movie: PlexAPI movie object
            position: Badge position ('northeast', 'northwest', etc.)
            force: Force reprocessing even if already has overlay

        Returns:
            True if successful
        """
        try:
            # Extract TMDB ID
            tmdb_id = self._extract_tmdb_id(movie.guids)
            if not tmdb_id:
                logger.warning(f"⚠️  {movie.title}: No TMDB ID found")
                return False

            # Check if already backed up (skip if force=False)
            if not force and self.backup_manager.has_backup(self.library_name, movie.title):
                logger.debug(f"⏭️  {movie.title}: Already processed (use force=True to reprocess)")
                return False

            # PRIORITY 1: Try to get ALL ratings from Plex's own metadata FIRST (fastest, most reliable)
            # This works for both movies AND TV shows and has ~100% coverage
            plex_ratings = self._extract_plex_ratings(movie)

            # Build ratings dict - start with what Plex has
            ratings = {}

            # Use Plex's TMDB rating if available
            if 'tmdb' in plex_ratings:
                ratings['tmdb'] = plex_ratings['tmdb']
            else:
                # PRIORITY 2: Fall back to TMDB API only if Plex doesn't have it
                # Determine media type (movie vs TV show)
                media_type = 'tv' if self.library.type == 'show' else 'movie'
                rating_data = self.rating_fetcher.fetch_tmdb_rating(tmdb_id, media_type=media_type)

                if not rating_data:
                    logger.warning(f"⚠️  {movie.title}: Failed to fetch TMDB rating")
                    return False

                tmdb_rating = rating_data['rating']
                if tmdb_rating == 0:
                    logger.warning(f"⚠️  {movie.title}: No TMDB rating available (0.0)")
                    return False

                ratings['tmdb'] = tmdb_rating

            # Use Plex's IMDb rating if available
            if 'imdb' in plex_ratings:
                ratings['imdb'] = plex_ratings['imdb']

            # Use Plex's RT scores if available
            if 'rt_critic' in plex_ratings:
                ratings['rt_critic'] = plex_ratings['rt_critic']
            if 'rt_audience' in plex_ratings:
                ratings['rt_audience'] = plex_ratings['rt_audience']

            # PRIORITY 2: Fall back to API calls for missing ratings
            imdb_id = self._extract_imdb_id(movie.guids)
            if imdb_id:
                # Get IMDb rating from OMDb if not already from Plex
                if 'imdb' not in ratings:
                    imdb_data = self.rating_fetcher.fetch_omdb_rating(imdb_id)
                    if imdb_data and imdb_data.get('imdb_rating'):
                        try:
                            ratings['imdb'] = float(imdb_data['imdb_rating'])
                        except:
                            pass

                # Get RT scores from MDBList if not already from Plex
                if 'rt_critic' not in ratings or 'rt_audience' not in ratings:
                    mdb_data = self.rating_fetcher.fetch_mdblist_rating(imdb_id)
                    if mdb_data:
                        if 'rt_critic' not in ratings and mdb_data.get('rt_critic'):
                            ratings['rt_critic'] = mdb_data['rt_critic']
                        if 'rt_audience' not in ratings and mdb_data.get('rt_audience'):
                            ratings['rt_audience'] = mdb_data['rt_audience']

            logger.info(f"Processing: {movie.title} (Ratings: {ratings})")

            if self.dry_run:
                logger.info(f"[DRY-RUN] Would apply multi-rating overlay to '{movie.title}': {ratings}")
                return True

            # Get poster URL
            poster_url = movie.posterUrl
            if not poster_url:
                logger.warning(f"⚠️  {movie.title}: No poster URL")
                return False

            # Backup original poster
            metadata = {
                'rating_key': movie.ratingKey,
                'tmdb_id': tmdb_id,
                'imdb_id': imdb_id,
                'title': movie.title,
                'year': movie.year,
                'ratings': ratings
            }

            original_path = self.backup_manager.backup_poster(
                library_name=self.library_name,
                item_title=movie.title,
                poster_url=poster_url,
                item_metadata=metadata,
                plex_token=self.plex_token,
                force=force
            )

            if not original_path:
                logger.error(f"✗ {movie.title}: Failed to backup poster")
                return False

            # Apply multi-rating overlay
            overlay_path = self.temp_dir / f"{movie.ratingKey}_overlay.jpg"
            self.multi_rating_badge.apply_to_poster(
                poster_path=str(original_path),
                ratings=ratings,
                output_path=str(overlay_path),
                position=position
            )

            # Save overlay version to backup
            self.backup_manager.save_overlay_poster(
                library_name=self.library_name,
                item_title=movie.title,
                overlay_image_path=str(overlay_path)
            )

            # Upload to Plex
            movie.uploadPoster(filepath=str(overlay_path))
            rating_str = ', '.join([f'{k.upper()}: {v:.1f}' for k, v in ratings.items()])
            logger.info(f"✓ {movie.title}: Multi-rating overlay applied ({rating_str})")

            # Cleanup temp file
            overlay_path.unlink()

            return True

        except Exception as e:
            logger.error(f"✗ {movie.title}: Error - {e}")
            return False

    def process_library(
        self,
        limit: Optional[int] = None,
        position: str = 'northwest',
        force: bool = False,
        rate_limit: float = 0.3
    ) -> Dict[str, int]:
        """
        Process entire library with rating overlays

        Args:
            limit: Max number of movies to process (None = all)
            position: Badge position
            force: Force reprocessing
            rate_limit: Delay between requests (seconds)

        Returns:
            Dict with statistics
        """
        all_movies = self.library.all()
        total = len(all_movies)

        if limit:
            all_movies = all_movies[:limit]
            print_header(f"Processing {limit} of {total} Movies")
        else:
            print_header(f"Processing All {total} Movies")

        # Initialize progress tracker
        progress = ProgressTracker(len(all_movies), "Applying rating overlays")
        start_time = time.time()

        print(f"Library: {self.library_name}")
        print(f"Backup Dir: {self.backup_manager.backup_dir}")
        print(f"Position: {position}")
        print(f"Force Reprocess: {force}")
        print()

        for i, movie in enumerate(all_movies, 1):
            # Show progress
            print_subheader(f"{progress.get_progress_str()} | {movie.title}")

            result = self.process_movie(movie, position=position, force=force)

            # Update progress
            if result:
                progress.update(success=True)
            else:
                # Check if skipped or failed
                if not force and self.backup_manager.has_backup(self.library_name, movie.title):
                    progress.update(skipped=True)
                else:
                    progress.update(success=False)

            # Show current stats
            print(f"  {progress.get_stats_str()}")

            # Rate limiting (respect TMDB limits)
            time.sleep(rate_limit)

        elapsed = time.time() - start_time

        # Final summary
        stats = {
            'Total Movies': len(all_movies),
            'Successfully Processed': progress.success,
            'Skipped (Already Done)': progress.skipped,
            'Failed': progress.failed,
            'Total Time': f"{elapsed:.1f}s ({elapsed/60:.1f}min)",
            'Average Speed': f"{elapsed/len(all_movies):.2f}s per movie",
            'Processing Rate': f"{len(all_movies)/elapsed:.2f} movies/sec"
        }

        print_summary(stats)

        return {
            'total': len(all_movies),
            'success': progress.success,
            'skipped': progress.skipped,
            'failed': progress.failed,
            'elapsed': elapsed
        }

    def restore_movie(self, movie_title: str) -> bool:
        """
        Restore original poster for a movie

        Args:
            movie_title: Movie title

        Returns:
            True if restored
        """
        # Find movie in library
        try:
            movie = self.library.get(movie_title)
        except Exception as e:
            logger.error(f"Movie not found: {movie_title}")
            return False

        if self.dry_run:
            logger.info(f"[DRY-RUN] Would restore original poster for '{movie_title}'")
            return True

        return self.backup_manager.restore_original(
            library_name=self.library_name,
            item_title=movie_title,
            plex_item=movie
        )

    def restore_library(self) -> int:
        """
        Restore all original posters in library

        Returns:
            Number of posters restored
        """
        backups = self.backup_manager.list_backups(library_name=self.library_name)
        restored_count = 0

        logger.info(f"Restoring {len(backups)} original posters...")

        for backup in backups:
            if self.restore_movie(backup['title']):
                restored_count += 1

        logger.info(f"✓ Restored {restored_count}/{len(backups)} posters")
        return restored_count

    def list_backups(self) -> List[Dict]:
        """List all backed up posters"""
        return self.backup_manager.list_backups(library_name=self.library_name)


def main():
    """Example usage"""
    import json
    import argparse
    from ..utils.logger import setup_logger

    # Parse arguments
    parser = argparse.ArgumentParser(description='Kometizarr Plex Poster Manager')
    parser.add_argument('--config', default='config.json', help='Config file path')
    parser.add_argument('--dry-run', action='store_true', help='Preview without applying')
    parser.add_argument('--limit', type=int, help='Limit number of movies to process')
    parser.add_argument('--force', action='store_true', help='Force reprocess all movies')
    parser.add_argument('--restore', action='store_true', help='Restore original posters')
    parser.add_argument('--restore-movie', type=str, help='Restore specific movie')
    args = parser.parse_args()

    # Load config
    with open(args.config) as f:
        config = json.load(f)

    # Setup better logging
    setup_logger('kometizarr', level=logging.INFO)

    # Initialize manager
    manager = PlexPosterManager(
        plex_url=config['plex']['url'],
        plex_token=config['plex']['token'],
        library_name=config['plex']['library'],
        tmdb_api_key=config['apis']['tmdb']['api_key'],
        omdb_api_key=config['apis'].get('omdb', {}).get('api_key'),
        mdblist_api_key=config['apis'].get('mdblist', {}).get('api_key'),
        backup_dir=config['output']['directory'],
        badge_style=config['rating_overlay']['badge'].get('style', 'default'),
        dry_run=args.dry_run
    )

    # Restore mode
    if args.restore:
        manager.restore_library()
        return

    if args.restore_movie:
        manager.restore_movie(args.restore_movie)
        return

    # Process library
    if config['rating_overlay']['enabled']:
        position = config['rating_overlay']['badge'].get('position', 'northeast')

        manager.process_library(
            limit=args.limit,
            position=position,
            force=args.force
        )


if __name__ == '__main__':
    main()
