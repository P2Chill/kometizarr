#!/usr/bin/env python3
"""
End-to-end test: Fetch poster from TMDB, add rating overlay
"""

import requests
from prototype_rating_overlay import RatingOverlay

# Configuration
TMDB_API_KEY = "dd6579eab556fb98a501e605ef8d2386"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

# Test movie
MOVIE_ID = 278  # The Shawshank Redemption
MOVIE_NAME = "The Shawshank Redemption"

print(f"=== Testing End-to-End: {MOVIE_NAME} ===\n")

# Initialize overlay system
overlay = RatingOverlay(TMDB_API_KEY)

# Step 1: Fetch movie data including poster path
print("Step 1: Fetching movie data...")
movie_url = f"https://api.themoviedb.org/3/movie/{MOVIE_ID}?api_key={TMDB_API_KEY}"
response = requests.get(movie_url)
data = response.json()

rating = data.get('vote_average')
poster_path = data.get('poster_path')
title = data.get('title')

print(f"✓ Title: {title}")
print(f"✓ Rating: {rating}/10")
print(f"✓ Poster path: {poster_path}\n")

# Step 2: Download poster
print("Step 2: Downloading poster...")
poster_url = f"{TMDB_IMAGE_BASE}{poster_path}"
poster_response = requests.get(poster_url)

with open('/tmp/original_poster.jpg', 'wb') as f:
    f.write(poster_response.content)

print(f"✓ Downloaded: /tmp/original_poster.jpg\n")

# Step 3: Apply rating overlay
print("Step 3: Applying rating overlay...")
overlay.apply_rating_to_poster(
    poster_path='/tmp/original_poster.jpg',
    rating=rating,
    output_path='/tmp/poster_with_rating.jpg',
    position='northeast'
)

print("\n" + "="*60)
print("✅ SUCCESS!")
print("\nGenerated files:")
print("  Original: /tmp/original_poster.jpg")
print("  With rating: /tmp/poster_with_rating.jpg")
print("\nRun this to view the result:")
print("  wsl.exe -d Ubuntu -e wslview /tmp/poster_with_rating.jpg")
