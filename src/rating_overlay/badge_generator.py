"""
Badge Generator - Create rating badge overlays

Based on demo_rating_badge.py and prototype_rating_overlay.py
MIT License - Copyright (c) 2026 Kometizarr Contributors
"""

from PIL import Image, ImageDraw, ImageFont
from typing import Tuple, Dict


class BadgeGenerator:
    """Generate rating badge images"""

    # Badge style presets
    STYLES = {
        'default': {
            'bg_color': (0, 0, 0, 180),
            'text_color': (255, 255, 255, 255),
            'star_color': (255, 215, 0, 255),
            'radius': 20
        },
        'imdb': {
            'bg_color': (245, 197, 24, 230),
            'text_color': (0, 0, 0, 255),
            'star_color': (0, 0, 0, 255),
            'radius': 15
        },
        'rt_fresh': {
            'bg_color': (250, 80, 80, 230),
            'text_color': (255, 255, 255, 255),
            'star_color': (255, 255, 255, 255),
            'radius': 20
        },
        'minimal': {
            'bg_color': (30, 30, 30, 200),
            'text_color': (255, 255, 255, 255),
            'star_color': (255, 255, 0, 255),
            'radius': 25
        }
    }

    def __init__(self, style: str = 'default'):
        """
        Initialize badge generator

        Args:
            style: Badge style ('default', 'imdb', 'rt_fresh', 'minimal')
        """
        self.style = style
        self.config = self.STYLES.get(style, self.STYLES['default'])

    def create_rating_badge(
        self,
        rating: float,
        size: Tuple[int, int] = (300, 120),
        format: str = "star"
    ) -> Image.Image:
        """
        Create a rating badge image

        Args:
            rating: Rating value (0-10 for star, 0-100 for percentage)
            size: Badge size (width, height)
            format: 'star' for ⭐ 8.5/10 or 'percent' for 🍅 95%

        Returns:
            PIL Image with transparent background
        """
        # Create transparent image
        img = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Background rounded rectangle
        padding = 10
        draw.rounded_rectangle(
            [(padding, padding), (size[0]-padding, size[1]-padding)],
            radius=self.config['radius'],
            fill=self.config['bg_color']
        )

        # Load fonts
        try:
            font_large = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60
            )
            font_small = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30
            )
        except:
            # Fallback to default font
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()

        if format == "star":
            self._draw_star_format(draw, rating, size, font_large, font_small)
        elif format == "percent":
            self._draw_percent_format(draw, rating, size, font_large, font_small)

        return img

    def _draw_star_format(
        self,
        draw: ImageDraw.Draw,
        rating: float,
        size: Tuple[int, int],
        font_large: ImageFont.FreeTypeFont,
        font_small: ImageFont.FreeTypeFont
    ):
        """Draw star format: ⭐ 8.5/10"""
        # Draw star
        star_text = "⭐"
        star_bbox = draw.textbbox((0, 0), star_text, font=font_large)
        star_x = 30
        star_y = (size[1] - (star_bbox[3] - star_bbox[1])) // 2
        draw.text(
            (star_x, star_y),
            star_text,
            font=font_large,
            fill=self.config['star_color']
        )

        # Draw rating number
        rating_text = f"{rating:.1f}"
        star_width = star_bbox[2] - star_bbox[0]
        rating_bbox = draw.textbbox((0, 0), rating_text, font=font_large)
        rating_x = star_x + star_width + 10
        rating_y = (size[1] - (rating_bbox[3] - rating_bbox[1])) // 2
        draw.text(
            (rating_x, rating_y),
            rating_text,
            font=font_large,
            fill=self.config['text_color']
        )

        # Draw /10 subscript
        subscript_text = "/10"
        rating_width = rating_bbox[2] - rating_bbox[0]
        subscript_x = rating_x + rating_width + 5
        subscript_y = rating_y + 20
        draw.text(
            (subscript_x, subscript_y),
            subscript_text,
            font=font_small,
            fill=self.config['text_color']
        )

    def _draw_percent_format(
        self,
        draw: ImageDraw.Draw,
        rating: float,
        size: Tuple[int, int],
        font_large: ImageFont.FreeTypeFont,
        font_small: ImageFont.FreeTypeFont
    ):
        """Draw percent format: 🍅 95%"""
        # Draw tomato emoji
        emoji_text = "🍅"
        emoji_bbox = draw.textbbox((0, 0), emoji_text, font=font_large)
        emoji_x = 30
        emoji_y = (size[1] - (emoji_bbox[3] - emoji_bbox[1])) // 2
        draw.text(
            (emoji_x, emoji_y),
            emoji_text,
            font=font_large,
            fill=self.config['star_color']
        )

        # Draw percentage
        percent_text = f"{int(rating)}%"
        emoji_width = emoji_bbox[2] - emoji_bbox[0]
        percent_x = emoji_x + emoji_width + 10
        percent_y = (size[1] - draw.textbbox((0, 0), percent_text, font=font_large)[3]) // 2
        draw.text(
            (percent_x, percent_y),
            percent_text,
            font=font_large,
            fill=self.config['text_color']
        )
