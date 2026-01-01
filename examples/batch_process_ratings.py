#!/usr/bin/env python3
"""
Batch process multiple movies with rating overlays
Demonstrates automation capability for large libraries
"""

import requests
from prototype_rating_overlay import RatingOverlay
from pathlib import Path
import time

# Configuration
TMDB_API_KEY = "dd6579eab556fb98a501e605ef8d2386"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"
OUTPUT_DIR = Path("/tmp/rated_posters")
OUTPUT_DIR.mkdir(exist_ok=True)

# Sample library (would be 26,000 movies in production)
SAMPLE_LIBRARY = [
    {'id': 278, 'name': 'The Shawshank Redemption'},
    {'id': 238, 'name': 'The Godfather'},
    {'id': 155, 'name': 'The Dark Knight'},
    {'id': 27205, 'name': 'Inception'},
    {'id': 13, 'name': 'Forrest Gump'},
    {'id': 496243, 'name': 'Parasite'},
    {'id': 129, 'name': 'Spirited Away'},
    {'id': 19404, 'name': 'Dilwale Dulhania Le Jayenge'},
    {'id': 372058, 'name': 'Your Name'},
    {'id': 389, 'name': '12 Angry Men'}
]

def process_movie(overlay, movie_id, movie_name):
    """Process a single movie"""
    try:
        # Fetch movie data
        movie_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}"
        response = requests.get(movie_url)
        data = response.json()

        rating = data.get('vote_average')
        poster_path = data.get('poster_path')

        if not poster_path:
            print(f"  ⚠️  {movie_name}: No poster available")
            return False

        # Download poster
        poster_url = f"{TMDB_IMAGE_BASE}{poster_path}"
        poster_response = requests.get(poster_url)

        original_path = OUTPUT_DIR / f"{movie_id}_original.jpg"
        with open(original_path, 'wb') as f:
            f.write(poster_response.content)

        # Apply rating overlay
        output_path = OUTPUT_DIR / f"{movie_id}_rated.jpg"
        overlay.apply_rating_to_poster(
            poster_path=str(original_path),
            rating=rating,
            output_path=str(output_path),
            position='northeast'
        )

        print(f"  ✓  {movie_name}: {rating}/10")
        return True

    except Exception as e:
        print(f"  ✗  {movie_name}: Error - {e}")
        return False


def main():
    print("=== Batch Rating Overlay Processor ===")
    print(f"Processing {len(SAMPLE_LIBRARY)} movies (in production: ~26,000)\n")

    overlay = RatingOverlay(TMDB_API_KEY)

    start_time = time.time()
    success_count = 0

    for i, movie in enumerate(SAMPLE_LIBRARY, 1):
        print(f"[{i}/{len(SAMPLE_LIBRARY)}] Processing...")
        if process_movie(overlay, movie['id'], movie['name']):
            success_count += 1

        # Respect TMDB rate limit (40 requests/10 seconds)
        time.sleep(0.3)  # ~3 requests/second = safe

    elapsed = time.time() - start_time

    print("\n" + "="*60)
    print(f"✅ Batch complete!")
    print(f"\nProcessed: {success_count}/{len(SAMPLE_LIBRARY)} movies")
    print(f"Time: {elapsed:.1f} seconds")
    print(f"Average: {elapsed/len(SAMPLE_LIBRARY):.1f} seconds/movie")

    # Estimate for full library
    full_library_time = (26000 * elapsed) / len(SAMPLE_LIBRARY)
    hours = full_library_time / 3600
    print(f"\n📊 Estimated time for 26,000 movies: {hours:.1f} hours")
    print(f"   (Can run overnight or in background)")

    print(f"\n📁 Output directory: {OUTPUT_DIR}")
    print(f"   Original posters: {OUTPUT_DIR}/*_original.jpg")
    print(f"   Rated posters: {OUTPUT_DIR}/*_rated.jpg")


if __name__ == '__main__':
    main()
