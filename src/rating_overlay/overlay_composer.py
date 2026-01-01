"""
Overlay Composer - Composite rating badges onto posters

Based on prototype_rating_overlay.py
MIT License - Copyright (c) 2026 Kometizarr Contributors
"""

from PIL import Image
from typing import Tuple, Literal
from .badge_generator import BadgeGenerator


class OverlayComposer:
    """Composite rating badges onto movie/TV show posters"""

    def __init__(self, badge_generator: BadgeGenerator = None):
        """
        Initialize overlay composer

        Args:
            badge_generator: BadgeGenerator instance (creates default if None)
        """
        self.badge_generator = badge_generator or BadgeGenerator()

    def apply_rating_to_poster(
        self,
        poster_path: str,
        rating: float,
        output_path: str,
        position: Literal['northeast', 'northwest', 'southeast', 'southwest'] = 'northeast',
        badge_format: str = 'star'
    ) -> Image.Image:
        """
        Apply rating badge to a poster image

        Args:
            poster_path: Path to input poster image
            rating: Rating value (0-10 for star, 0-100 for percent)
            output_path: Path to save output image
            position: Badge position ('northeast', 'northwest', 'southeast', 'southwest')
            badge_format: 'star' or 'percent'

        Returns:
            PIL Image of the result
        """
        # Open poster
        poster = Image.open(poster_path).convert('RGBA')
        poster_width, poster_height = poster.size

        print(f"✓ Loaded poster: {poster_path} ({poster_width}x{poster_height})")

        # Create rating badge (15% of poster width)
        badge_width = int(poster_width * 0.15)
        badge_height = int(badge_width * 0.4)  # Maintain aspect ratio
        badge = self.badge_generator.create_rating_badge(
            rating,
            size=(badge_width, badge_height),
            format=badge_format
        )

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

        # Composite badge onto poster (use badge as mask for transparency)
        poster.paste(badge, (badge_x, badge_y), badge)

        # Save result
        poster_rgb = poster.convert('RGB')  # Convert back to RGB for JPEG
        poster_rgb.save(output_path, 'JPEG', quality=95)

        print(f"✓ Applied rating overlay: {output_path}")
        print(f"  Position: {position} ({badge_x}, {badge_y})")

        return poster

    def apply_multiple_ratings(
        self,
        poster_path: str,
        ratings: dict,
        output_path: str,
        layout: str = 'stacked'
    ):
        """
        Apply multiple rating badges to a poster (e.g., TMDB + IMDb + RT)

        Args:
            poster_path: Path to input poster image
            ratings: Dict of ratings {'tmdb': 8.5, 'imdb': 8.7, 'rt': 95}
            output_path: Path to save output image
            layout: 'stacked' (vertical) or 'row' (horizontal)

        Returns:
            PIL Image of the result
        """
        # TODO: Implement multi-badge layout
        # For now, just apply the first available rating
        if 'tmdb' in ratings:
            return self.apply_rating_to_poster(
                poster_path,
                ratings['tmdb'],
                output_path,
                position='northeast'
            )
        elif 'imdb' in ratings:
            return self.apply_rating_to_poster(
                poster_path,
                float(ratings['imdb']),
                output_path,
                position='northeast'
            )

        raise ValueError("No valid ratings provided")
