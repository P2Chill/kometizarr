"""
Poster Backup Manager - Safely backup and restore Plex posters

Inspired by Posterizarr's backup system
MIT License - Copyright (c) 2026 Kometizarr Contributors
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict
import requests
from PIL import Image

logger = logging.getLogger(__name__)


class PosterBackupManager:
    """Manage poster backups before applying overlays"""

    def __init__(self, backup_dir: str = '/backups'):
        """
        Initialize backup manager

        Args:
            backup_dir: Root directory for backups
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Backup directory: {self.backup_dir}")

    def _get_backup_path(self, library_name: str, item_title: str, item_type: str = 'movie') -> Path:
        """
        Get backup path for an item

        Args:
            library_name: Plex library name (e.g., 'Movies')
            item_title: Movie/show title
            item_type: 'movie', 'show', 'season', 'episode'

        Returns:
            Path object for backup directory
        """
        # Sanitize title for filesystem
        safe_title = "".join(c for c in item_title if c.isalnum() or c in (' ', '-', '_')).strip()
        return self.backup_dir / library_name / safe_title

    def _save_metadata(self, backup_path: Path, metadata: Dict):
        """Save metadata JSON alongside backup"""
        metadata_file = backup_path / 'metadata.json'
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)

    def _load_metadata(self, backup_path: Path) -> Optional[Dict]:
        """Load metadata JSON from backup"""
        metadata_file = backup_path / 'metadata.json'
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                return json.load(f)
        return None

    def has_backup(self, library_name: str, item_title: str) -> bool:
        """
        Check if backup already exists

        Args:
            library_name: Plex library name
            item_title: Item title

        Returns:
            True if backup exists
        """
        backup_path = self._get_backup_path(library_name, item_title)
        original_path = backup_path / 'poster_original.jpg'
        return original_path.exists()

    def has_overlay(self, library_name: str, item_title: str) -> bool:
        """
        Check if overlay version exists (item already processed)

        Args:
            library_name: Plex library name
            item_title: Item title

        Returns:
            True if overlay backup exists
        """
        backup_path = self._get_backup_path(library_name, item_title)
        overlay_path = backup_path / 'poster_overlay.jpg'
        return overlay_path.exists()

    def backup_poster(
        self,
        library_name: str,
        item_title: str,
        poster_url: str,
        item_metadata: Dict,
        plex_token: str,
        force: bool = False
    ) -> Optional[Path]:
        """
        Download and backup original poster from Plex

        Args:
            library_name: Plex library name
            item_title: Item title
            poster_url: Plex poster URL
            item_metadata: Metadata dict (rating_key, tmdb_id, etc.)
            plex_token: Plex authentication token
            force: Force re-download even if backup exists

        Returns:
            Path to backed up poster, or None if error
        """
        backup_path = self._get_backup_path(library_name, item_title)
        backup_path.mkdir(parents=True, exist_ok=True)

        original_path = backup_path / 'poster_original.jpg'

        # Skip if already backed up (unless force=True)
        if original_path.exists() and not force:
            logger.debug(f"Backup already exists: {item_title}")
            return original_path

        try:
            # Download original poster from Plex
            logger.info(f"Backing up poster: {item_title}")

            # Add auth token to URL
            if '?' in poster_url:
                download_url = f"{poster_url}&X-Plex-Token={plex_token}"
            else:
                download_url = f"{poster_url}?X-Plex-Token={plex_token}"

            response = requests.get(download_url, timeout=30)
            response.raise_for_status()

            # Save original
            with open(original_path, 'wb') as f:
                f.write(response.content)

            # Verify it's a valid image
            try:
                img = Image.open(original_path)
                img.verify()
            except Exception as e:
                logger.error(f"Downloaded file is not a valid image: {e}")
                original_path.unlink()
                return None

            # Save metadata
            metadata = {
                'backed_up_at': datetime.now().isoformat(),
                'library_name': library_name,
                'item_title': item_title,
                **item_metadata
            }
            self._save_metadata(backup_path, metadata)

            logger.info(f"✓ Backed up: {original_path}")
            return original_path

        except Exception as e:
            logger.error(f"✗ Failed to backup poster for '{item_title}': {e}")
            if original_path.exists():
                original_path.unlink()  # Clean up partial download
            return None

    def get_original_poster(self, library_name: str, item_title: str) -> Optional[Path]:
        """
        Get path to original poster backup

        Args:
            library_name: Plex library name
            item_title: Item title

        Returns:
            Path to original poster, or None if not found
        """
        backup_path = self._get_backup_path(library_name, item_title)
        original_path = backup_path / 'poster_original.jpg'

        if original_path.exists():
            return original_path
        return None

    def save_overlay_poster(
        self,
        library_name: str,
        item_title: str,
        overlay_image_path: str
    ) -> Optional[Path]:
        """
        Save the overlay version alongside original

        Args:
            library_name: Plex library name
            item_title: Item title
            overlay_image_path: Path to overlay version

        Returns:
            Path to saved overlay poster
        """
        backup_path = self._get_backup_path(library_name, item_title)
        overlay_path = backup_path / 'poster_overlay.jpg'

        try:
            # Copy overlay version to backup
            img = Image.open(overlay_image_path)
            img.save(overlay_path, 'JPEG', quality=95)

            logger.info(f"✓ Saved overlay version: {overlay_path}")
            return overlay_path

        except Exception as e:
            logger.error(f"✗ Failed to save overlay for '{item_title}': {e}")
            return None

    def restore_original(self, library_name: str, item_title: str, plex_item) -> bool:
        """
        Restore original poster to Plex

        Args:
            library_name: Plex library name
            item_title: Item title
            plex_item: PlexAPI item object

        Returns:
            True if restored successfully
        """
        original_path = self.get_original_poster(library_name, item_title)

        if not original_path:
            logger.warning(f"No backup found for '{item_title}'")
            return False

        try:
            plex_item.uploadPoster(filepath=str(original_path))
            logger.info(f"✓ Restored original poster: {item_title}")

            # Delete the overlay file so has_overlay() returns False
            backup_path = self._get_backup_path(library_name, item_title)
            overlay_path = backup_path / 'poster_overlay.jpg'
            if overlay_path.exists():
                overlay_path.unlink()
                logger.debug(f"Cleaned up overlay backup: {overlay_path}")

            return True

        except Exception as e:
            logger.error(f"✗ Failed to restore poster for '{item_title}': {e}")
            return False

    def get_metadata(self, library_name: str, item_title: str) -> Optional[Dict]:
        """
        Get metadata for backed up item

        Args:
            library_name: Plex library name
            item_title: Item title

        Returns:
            Metadata dict or None
        """
        backup_path = self._get_backup_path(library_name, item_title)
        return self._load_metadata(backup_path)

    def list_backups(self, library_name: Optional[str] = None) -> list:
        """
        List all backups

        Args:
            library_name: Optional library filter

        Returns:
            List of backup info dicts
        """
        backups = []

        if library_name:
            library_path = self.backup_dir / library_name
            if not library_path.exists():
                return backups
            libraries = [library_path]
        else:
            libraries = [d for d in self.backup_dir.iterdir() if d.is_dir()]

        for lib_dir in libraries:
            for item_dir in lib_dir.iterdir():
                if not item_dir.is_dir():
                    continue

                original_path = item_dir / 'poster_original.jpg'
                overlay_path = item_dir / 'poster_overlay.jpg'

                if original_path.exists():
                    metadata = self._load_metadata(item_dir)
                    backups.append({
                        'library': lib_dir.name,
                        'title': item_dir.name,
                        'original_path': str(original_path),
                        'overlay_path': str(overlay_path) if overlay_path.exists() else None,
                        'metadata': metadata
                    })

        return backups

    def cleanup_backup(self, library_name: str, item_title: str) -> bool:
        """
        Delete backup for an item

        Args:
            library_name: Plex library name
            item_title: Item title

        Returns:
            True if deleted successfully
        """
        backup_path = self._get_backup_path(library_name, item_title)

        if not backup_path.exists():
            logger.warning(f"No backup found for '{item_title}'")
            return False

        try:
            import shutil
            shutil.rmtree(backup_path)
            logger.info(f"✓ Deleted backup: {item_title}")
            return True

        except Exception as e:
            logger.error(f"✗ Failed to delete backup for '{item_title}': {e}")
            return False
