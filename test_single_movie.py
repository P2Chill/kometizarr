#!/usr/bin/env python3
"""
Test rating overlay on a single movie

Quick test to verify the entire pipeline works before processing the whole library.
"""

import json
import logging
from src.rating_overlay.plex_poster_manager import PlexPosterManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    # Load config
    with open('config.json') as f:
        config = json.load(f)

    # Initialize manager
    manager = PlexPosterManager(
        plex_url=config['plex']['url'],
        plex_token=config['plex']['token'],
        library_name=config['plex']['library'],
        tmdb_api_key=config['apis']['tmdb']['api_key'],
        omdb_api_key=config['apis'].get('omdb', {}).get('api_key'),
        backup_dir=config['output']['directory'],
        badge_style=config['rating_overlay']['badge'].get('style', 'default'),
        dry_run=False  # Do it for real
    )

    print("\n" + "=" * 60)
    print("Testing Rating Overlay on Single Movie")
    print("=" * 60)

    # Get first movie from library
    all_movies = manager.library.all()
    if not all_movies:
        print("No movies found in library!")
        return

    # Test with first movie
    test_movie = all_movies[0]

    print(f"\nTest movie: {test_movie.title} ({test_movie.year})")
    print(f"Plex URL: {manager.plex_url}")
    print(f"Library: {manager.library_name}")
    print(f"Backup dir: {config['output']['directory']}")
    print(f"Badge style: {config['rating_overlay']['badge']['style']}")
    print(f"Badge position: {config['rating_overlay']['badge']['position']}")

    print("\n" + "-" * 60)
    print("Processing...")
    print("-" * 60 + "\n")

    # Process the movie
    success = manager.process_movie(
        movie=test_movie,
        position=config['rating_overlay']['badge']['position'],
        force=True  # Force reprocess for testing
    )

    print("\n" + "=" * 60)
    if success:
        print("✅ TEST PASSED!")
        print(f"\nMovie: {test_movie.title}")
        print(f"  Original poster backed up")
        print(f"  Rating overlay applied")
        print(f"  Uploaded to Plex")

        # Show backup info
        backups = manager.list_backups()
        if backups:
            print(f"\nBackup location:")
            print(f"  {backups[0]['original_path']}")
            if backups[0]['overlay_path']:
                print(f"  {backups[0]['overlay_path']}")
    else:
        print("❌ TEST FAILED!")
        print(f"\nCheck logs above for error details")

    print("=" * 60)

    print("\n💡 Next steps:")
    if success:
        print("  1. Check Plex - the poster should now have a rating badge")
        print("  2. Run 'python3 -m src.rating_overlay.plex_poster_manager --limit 10' to test with 10 movies")
        print("  3. Run 'python3 -m src.rating_overlay.plex_poster_manager' to process entire library")
        print("\n  To restore original:")
        print(f"    python3 -m src.rating_overlay.plex_poster_manager --restore-movie '{test_movie.title}'")
    else:
        print("  Fix the errors above and try again")


if __name__ == '__main__':
    main()
