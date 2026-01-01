#!/usr/bin/env python3
"""
Kometizarr Rating Overlay Prototype

This script demonstrates how to:
1. Fetch ratings from TMDB API
2. Generate a rating badge overlay
3. Composite it onto a movie poster
"""

import requests
from PIL import Image, ImageDraw, ImageFont
import io
import os
from pathlib import Path

# Configuration
TMDB_API_KEY = ""  # Will read from Posterizarr config
TMDB_BASE_URL = "https://api.themoviedb.org/3"

class RatingOverlay:
    def __init__(self, tmdb_api_key):
        self.api_key = tmdb_api_key

    def fetch_movie_rating(self, tmdb_id):
        """Fetch TMDB rating for a movie"""
        url = f"{TMDB_BASE_URL}/movie/{tmdb_id}?api_key={self.api_key}"

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            rating = data.get('vote_average', 0)
            vote_count = data.get('vote_count', 0)
            title = data.get('title', 'Unknown')

            print(f"✓ Fetched: {title}")
            print(f"  Rating: {rating}/10 ({vote_count} votes)")

            return {
                'rating': rating,
                'vote_count': vote_count,
                'title': title
            }
        except Exception as e:
            print(f"✗ Error fetching rating: {e}")
            return None

    def create_rating_badge(self, rating, output_path, size=(300, 120)):
        """Create a rating badge image with transparent background"""
        # Create transparent image
        img = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Background rounded rectangle (semi-transparent black)
        padding = 10
        bg_color = (0, 0, 0, 180)  # Black with 70% opacity
        draw.rounded_rectangle(
            [(padding, padding), (size[0]-padding, size[1]-padding)],
            radius=20,
            fill=bg_color
        )

        # Try to load a nice font, fallback to default
        try:
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # Draw star emoji (using text)
        star_text = "⭐"
        star_bbox = draw.textbbox((0, 0), star_text, font=font_large)
        star_width = star_bbox[2] - star_bbox[0]
        star_x = 30
        star_y = (size[1] - (star_bbox[3] - star_bbox[1])) // 2
        draw.text((star_x, star_y), star_text, font=font_large, fill=(255, 215, 0, 255))

        # Draw rating number
        rating_text = f"{rating:.1f}"
        rating_bbox = draw.textbbox((0, 0), rating_text, font=font_large)
        rating_x = star_x + star_width + 10
        rating_y = (size[1] - (rating_bbox[3] - rating_bbox[1])) // 2
        draw.text((rating_x, rating_y), rating_text, font=font_large, fill=(255, 255, 255, 255))

        # Draw "/10" subscript
        subscript_text = "/10"
        subscript_bbox = draw.textbbox((0, 0), subscript_text, font=font_small)
        subscript_x = rating_x + (rating_bbox[2] - rating_bbox[0]) + 5
        subscript_y = rating_y + 20
        draw.text((subscript_x, subscript_y), subscript_text, font=font_small, fill=(200, 200, 200, 255))

        # Save badge
        img.save(output_path)
        print(f"✓ Created rating badge: {output_path}")

        return img

    def apply_rating_to_poster(self, poster_path, rating, output_path, position='northeast'):
        """Apply rating badge to a poster image"""
        # Open poster
        poster = Image.open(poster_path).convert('RGBA')
        poster_width, poster_height = poster.size

        print(f"✓ Loaded poster: {poster_path} ({poster_width}x{poster_height})")

        # Create rating badge
        badge_width = int(poster_width * 0.15)  # 15% of poster width
        badge_height = int(badge_width * 0.4)   # Maintain aspect ratio
        badge = self.create_rating_badge(rating, '/tmp/rating_badge.png', size=(badge_width, badge_height))

        # Calculate position
        offset_x = int(poster_width * 0.03)  # 3% from edge
        offset_y = int(poster_height * 0.03)

        positions = {
            'northeast': (poster_width - badge_width - offset_x, offset_y),
            'northwest': (offset_x, offset_y),
            'southeast': (poster_width - badge_width - offset_x, poster_height - badge_height - offset_y),
            'southwest': (offset_x, poster_height - badge_height - offset_y)
        }

        badge_x, badge_y = positions.get(position, positions['northeast'])

        # Composite badge onto poster
        poster.paste(badge, (badge_x, badge_y), badge)  # Use badge as mask for transparency

        # Save result
        poster = poster.convert('RGB')  # Convert back to RGB for JPEG
        poster.save(output_path, 'JPEG', quality=95)

        print(f"✓ Applied rating overlay: {output_path}")
        print(f"  Position: {position} ({badge_x}, {badge_y})")

        return poster


def main():
    """Test the rating overlay system"""
    print("=== Kometizarr Rating Overlay Prototype ===\n")

    # Read TMDB API key from Posterizarr config
    config_path = Path(__file__).parent / "config.example.json"
    if config_path.exists():
        import json
        with open(config_path) as f:
            config = json.load(f)
            api_key = config['ApiPart']['tmdbtoken']
            print(f"✓ Loaded TMDB API key from config\n")
    else:
        print("✗ No config found - using placeholder")
        api_key = "YOUR_TMDB_API_KEY_HERE"

    # Initialize overlay system
    overlay = RatingOverlay(api_key)

    # Test movies (TMDB IDs)
    test_movies = [
        {'id': 278, 'name': 'The Shawshank Redemption'},
        {'id': 238, 'name': 'The Godfather'},
        {'id': 424, 'name': 'Schindler\'s List'}
    ]

    print("Testing rating fetch for sample movies:\n")

    for movie in test_movies:
        rating_data = overlay.fetch_movie_rating(movie['id'])
        if rating_data:
            print(f"  → {movie['name']}: {rating_data['rating']}/10\n")

    print("\n" + "="*50)
    print("To test with actual posters:")
    print("1. Get a TMDB API key from https://www.themoviedb.org/settings/api")
    print("2. Update config.json with your API key")
    print("3. Run: python prototype_rating_overlay.py --poster /path/to/poster.jpg --tmdb-id 278 --output /tmp/test_poster.jpg")


if __name__ == '__main__':
    main()
