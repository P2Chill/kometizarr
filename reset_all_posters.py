#!/usr/bin/env python3
"""
Reset all Plex movie posters to TMDB defaults
"""
import json
from plexapi.server import PlexServer

# Load config
with open('config.json') as f:
    config = json.load(f)

# Connect to Plex
server = PlexServer(config['plex']['url'], config['plex']['token'])
library = server.library.section(config['plex']['library'])

print(f"Resetting all posters in '{config['plex']['library']}' library to TMDB defaults...")
print()

all_movies = library.all()
total = len(all_movies)
success = 0
failed = 0

for i, movie in enumerate(all_movies, 1):
    try:
        # Get all available posters
        posters = movie.posters()

        # Find TMDB poster (usually first one with tmdb in URL)
        tmdb_poster = None
        for poster in posters:
            # Check if it's a TMDB poster URL
            if 'tmdb' in str(poster.ratingKey).lower() or 'image.tmdb.org' in str(poster.ratingKey):
                tmdb_poster = poster
                break

        if tmdb_poster:
            # Select the TMDB poster
            movie.setPoster(tmdb_poster)
            success += 1
            print(f"[{i}/{total}] ✓ {movie.title}")
        else:
            # No TMDB poster found, just unlock
            movie.unlockPoster()
            success += 1
            print(f"[{i}/{total}] ⚠ {movie.title} (no TMDB poster, unlocked)")
    except Exception as e:
        failed += 1
        print(f"[{i}/{total}] ✗ {movie.title}: {e}")

print()
print(f"Reset complete!")
print(f"  Success: {success}")
print(f"  Failed: {failed}")
print(f"  Total: {total}")
