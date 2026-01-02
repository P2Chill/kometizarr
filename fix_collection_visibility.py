#!/usr/bin/env python3
"""
Fix collection visibility - hide collections from library tab

Collections should only appear in the Collections tab, not clutter the library view.
"""

import json
from plexapi.server import PlexServer

# Load config
with open('config.json') as f:
    config = json.load(f)

# Connect to Plex
server = PlexServer(config['plex']['url'], config['plex']['token'])
library = server.library.section(config['plex']['library'])

print("Fixing collection visibility...")
print("Collections should only show in Collections tab, not Library tab\n")

# Get all collections
collections = library.collections()

for collection in collections:
    try:
        # Hide from library, keep in collections tab
        collection.modeUpdate(mode='hide')
        print(f"✓ Hidden from library: {collection.title}")
    except Exception as e:
        print(f"✗ Failed to update {collection.title}: {e}")

print(f"\n✅ Updated {len(collections)} collections")
print("Collections will now only appear in the Collections tab")
