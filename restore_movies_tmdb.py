#!/usr/bin/env python3
"""Restore Movies library to TMDB posters"""
import os
import sys
from plexapi.server import PlexServer
import time

plex_url = os.getenv('PLEX_URL', 'http://192.168.1.20:32400')
plex_token = os.getenv('PLEX_TOKEN')

server = PlexServer(plex_url, plex_token)
library = server.library.section('Movies')
all_items = library.all()

print(f'Starting Movies: {len(all_items)} items', flush=True)

restored = 0
skipped = 0
failed = 0

for i, item in enumerate(all_items, 1):
    try:
        posters = item.posters()

        # Find first non-uploaded poster (TMDB)
        original_poster = None
        for poster in posters:
            if 'upload' not in poster.ratingKey:
                original_poster = poster
                break

        if original_poster:
            original_poster.select()
            restored += 1
        else:
            skipped += 1

        if i % 100 == 0:
            print(f'Movies: {i}/{len(all_items)} - Restored: {restored}, Skipped: {skipped}', flush=True)

    except Exception as e:
        failed += 1
        if failed < 5:  # Only print first few errors
            print(f'Error on {item.title}: {e}', flush=True)

    time.sleep(0.1)

print(f'Movies DONE: Restored {restored}, Skipped {skipped}, Failed {failed}', flush=True)
