"""
Multi-Rating Badge Generator - Create Kometa-style rating overlays with multiple sources

Supports TMDB, IMDb, and Rotten Tomatoes ratings with logos
MIT License - Copyright (c) 2026 Kometizarr Contributors
"""

from PIL import Image, ImageDraw, ImageFont
from typing import Tuple, Dict, Optional, List, Any
from pathlib import Path


class MultiRatingBadge:
    """Generate rating badges with multiple sources (TMDB, IMDb, RT)"""

    def __init__(self, assets_dir: str = None):
        """
        Initialize multi-rating badge generator

        Args:
            assets_dir: Path to assets directory with logos
        """
        if assets_dir:
            self.assets_dir = Path(assets_dir)
        else:
            # Try Docker mount path first, fall back to local development path
            docker_path = Path('/app/kometizarr/assets/logos')
            if docker_path.exists():
                self.assets_dir = docker_path
            else:
                # Local development - relative to this file
                self.assets_dir = Path(__file__).parent.parent.parent / 'assets' / 'logos'

        # Load logos
        self.logos = self._load_logos()

    def _load_logos(self) -> Dict[str, Optional[Image.Image]]:
        """Load rating source logos"""
        logos = {}

        logo_files = {
            'tmdb': 'tmdb.png',
            'imdb': 'imdb.png',
            'rt_fresh': 'rt_fresh.png',
            'rt_rotten': 'rt_rotten.png',
            'rt_audience_fresh': 'rt_audience_fresh.png',
            'rt_audience_rotten': 'rt_audience_rotten.png'
        }

        for source, filename in logo_files.items():
            logo_path = self.assets_dir / filename
            if logo_path.exists():
                try:
                    logos[source] = Image.open(logo_path).convert('RGBA')
                except Exception as e:
                    print(f"Failed to load {source} logo: {e}")
                    logos[source] = None
            else:
                logos[source] = None

        return logos

    def _draw_text_with_shadow(
        self,
        draw: ImageDraw.Draw,
        position: Tuple[int, int],
        text: str,
        font: ImageFont.FreeTypeFont,
        color: Tuple[int, int, int, int],
        shadow_offset: int = 6,
        anchor: str = "lm",
        stroke_width: int = None
    ):
        """Draw text with drop shadow for better visibility"""
        x, y = position

        # Auto-scale stroke width if not provided
        if stroke_width is None:
            stroke_width = max(2, shadow_offset // 2)

        # Draw shadow (slightly offset, darker)
        draw.text(
            (x + shadow_offset, y + shadow_offset),
            text,
            font=font,
            fill=(0, 0, 0, 200),  # Dark shadow
            anchor=anchor,
            stroke_width=stroke_width + 1,
            stroke_fill=(0, 0, 0, 255)
        )

        # Draw main text
        draw.text(
            (x, y),
            text,
            font=font,
            fill=color,
            anchor=anchor,
            stroke_width=stroke_width,
            stroke_fill=(0, 0, 0, 200)  # Outline for extra visibility
        )

    def create_multi_rating_badge(
        self,
        ratings: Dict[str, float],
        poster_size: Tuple[int, int],
        position: str = 'northeast',
        badge_style: Optional[Dict[str, Any]] = None
    ) -> Image.Image:
        """
        Create a badge with multiple rating sources

        Args:
            ratings: Dict like {'tmdb': 7.2, 'imdb': 7.5, 'rt': 85}
            poster_size: (width, height) of poster
            position: Badge position
            badge_style: Optional styling options (badge_width_percent, font_size_multiplier, rating_color, background_opacity)

        Returns:
            PIL Image with transparent background
        """
        poster_width, poster_height = poster_size

        # Apply custom styling or use defaults
        style = badge_style or {}
        badge_width_percent = style.get('badge_width_percent', 35) / 100  # Convert percentage to decimal
        font_multiplier = style.get('font_size_multiplier', 1.0)
        rating_color_hex = style.get('rating_color', '#FFD700')  # Gold
        background_opacity = style.get('background_opacity', 128)

        # Convert hex color to RGB tuple
        rating_color = tuple(int(rating_color_hex.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + (255,)

        # Badge size scales with poster width (customizable)
        badge_width = int(poster_width * badge_width_percent)

        # Calculate height based on number of ratings
        # Scale row height proportionally with badge width
        num_ratings = len(ratings)
        row_height = int(badge_width * 0.27)  # Proportional to width
        padding = int(badge_width * 0.03)
        badge_height = (num_ratings * row_height) + (padding * 2)

        # Create badge with transparent background
        badge = Image.new('RGBA', (badge_width, badge_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(badge)

        # Draw semi-transparent black rounded rectangle background
        corner_radius = int(badge_width * 0.05)  # 5% of badge width
        draw.rounded_rectangle(
            [(0, 0), (badge_width, badge_height)],
            radius=corner_radius,
            fill=(0, 0, 0, background_opacity)  # Customizable opacity
        )

        # Load fonts - scale with badge size and custom multiplier
        font_large_size = int(badge_width * 0.20 * font_multiplier)  # 20% of badge width * multiplier
        font_small_size = int(badge_width * 0.10 * font_multiplier)  # 10% of badge width * multiplier

        try:
            font_large = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_large_size
            )
            font_small = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_small_size
            )
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # Draw each rating
        y_offset = padding
        for source, rating in ratings.items():
            self._draw_rating_row(
                badge, draw, source, rating,
                y_offset, badge_width, row_height,
                font_large, font_small, badge_width,  # Pass badge_width for scaling
                rating_color  # Pass custom rating color
            )
            y_offset += row_height

        return badge

    def create_individual_badge(
        self,
        source: str,
        rating: float,
        poster_size: Tuple[int, int],
        badge_style: Optional[Dict[str, Any]] = None
    ) -> Image.Image:
        """
        Create a single compact badge with logo on top, rating underneath

        Args:
            source: Rating source ('tmdb', 'imdb', 'rt_critic', 'rt_audience')
            rating: Rating value
            poster_size: (width, height) of poster for scaling
            badge_style: Optional styling options

        Returns:
            PIL Image with transparent background
        """
        poster_width, poster_height = poster_size

        # Apply custom styling or use defaults
        style = badge_style or {}
        badge_size_percent = style.get('individual_badge_size', 12) / 100  # 12% of poster width by default
        font_multiplier = style.get('font_size_multiplier', 1.0)
        rating_color_hex = style.get('rating_color', '#FFD700')  # Gold
        background_opacity = style.get('background_opacity', 128)

        # Convert hex color to RGB tuple
        rating_color = tuple(int(rating_color_hex.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + (255,)

        # Badge size - compact square-ish badge
        badge_width = int(poster_width * badge_size_percent)
        badge_height = int(badge_width * 1.4)  # Slightly taller than wide (logo + number)

        # Create badge with transparent background
        badge = Image.new('RGBA', (badge_width, badge_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(badge)

        # Draw semi-transparent black rounded rectangle background
        corner_radius = int(badge_width * 0.1)  # 10% of badge width
        draw.rounded_rectangle(
            [(0, 0), (badge_width, badge_height)],
            radius=corner_radius,
            fill=(0, 0, 0, background_opacity)
        )

        # For RT scores, dynamically select logo based on score
        logo_key = source
        if source == 'rt_critic':
            logo_key = 'rt_fresh' if rating >= 60 else 'rt_rotten'
        elif source == 'rt_audience':
            logo_key = 'rt_audience_fresh' if rating >= 60 else 'rt_audience_rotten'

        # Draw logo in top 60% of badge
        logo = self.logos.get(logo_key)
        logo_section_height = int(badge_height * 0.6)
        padding = int(badge_width * 0.1)

        if logo:
            # Calculate logo size to fit in top section
            max_logo_size = min(badge_width - (padding * 2), logo_section_height - padding)

            # Resize logo maintaining aspect ratio
            orig_width, orig_height = logo.size
            aspect_ratio = orig_width / orig_height

            if aspect_ratio > 1:
                # Wider than tall
                logo_width = max_logo_size
                logo_height = int(max_logo_size / aspect_ratio)
            else:
                # Taller than wide or square
                logo_height = max_logo_size
                logo_width = int(max_logo_size * aspect_ratio)

            logo_resized = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)

            # Center logo in top section
            logo_x = (badge_width - logo_width) // 2
            logo_y = (logo_section_height - logo_height) // 2

            badge.paste(logo_resized, (logo_x, logo_y), logo_resized)

        # Draw rating in bottom 40% of badge
        number_section_top = logo_section_height
        number_section_height = badge_height - logo_section_height

        # Load font
        font_size = int(badge_width * 0.35 * font_multiplier)  # 35% of badge width
        try:
            font_rating = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size
            )
            font_percent = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(font_size * 0.6)
            )
        except:
            font_rating = ImageFont.load_default()
            font_percent = ImageFont.load_default()

        # Format rating
        if source in ['rt_critic', 'rt_audience']:
            rating_text = f"{int(rating)}"
            percent_text = "%"
        else:
            rating_text = f"{rating:.1f}"
            percent_text = ""

        # Center position in bottom section
        center_x = badge_width // 2
        center_y = number_section_top + (number_section_height // 2)

        # Calculate total text width if there's a percent sign
        if percent_text:
            rating_bbox = draw.textbbox((0, 0), rating_text, font=font_rating)
            percent_bbox = draw.textbbox((0, 0), percent_text, font=font_percent)
            total_width = (rating_bbox[2] - rating_bbox[0]) + (percent_bbox[2] - percent_bbox[0]) + 2

            # Draw number (left side)
            self._draw_text_with_shadow(
                draw,
                (center_x - total_width // 2, center_y),
                rating_text,
                font_rating,
                rating_color,
                shadow_offset=max(2, int(badge_width * 0.02)),
                anchor="lm"
            )

            # Draw % (right side)
            self._draw_text_with_shadow(
                draw,
                (center_x + total_width // 2 - (percent_bbox[2] - percent_bbox[0]), center_y + int(font_size * 0.1)),
                percent_text,
                font_percent,
                (255, 255, 255, 255),
                shadow_offset=max(1, int(badge_width * 0.01)),
                anchor="lm"
            )
        else:
            # Just center the number
            self._draw_text_with_shadow(
                draw,
                (center_x, center_y),
                rating_text,
                font_rating,
                rating_color,
                shadow_offset=max(2, int(badge_width * 0.02)),
                anchor="mm"  # Middle-middle anchor
            )

        return badge

    def _draw_rating_row(
        self,
        badge: Image.Image,
        draw: ImageDraw.Draw,
        source: str,
        rating: float,
        y_offset: int,
        badge_width: int,
        row_height: int,
        font_large: ImageFont.FreeTypeFont,
        font_small: ImageFont.FreeTypeFont,
        scale_width: int,  # Badge width for scaling
        rating_color: Tuple[int, int, int, int] = (255, 215, 0, 255)  # Default gold
    ):
        """Draw a single rating row with logo and score"""
        x_padding = int(scale_width * 0.03)  # Scale padding

        # For RT scores, dynamically select logo based on score AND source
        logo_key = source
        if source in ['rt', 'rt_critic']:
            # RT Critic uses tomato logos
            if rating >= 60:
                logo_key = 'rt_fresh'
            else:
                logo_key = 'rt_rotten'
        elif source == 'rt_audience':
            # RT Audience uses popcorn logos
            if rating >= 60:
                logo_key = 'rt_audience_fresh'
            else:
                logo_key = 'rt_audience_rotten'

        # Draw logo - scale with badge size for consistency
        logo = self.logos.get(logo_key)
        max_logo_width = int(scale_width * 0.40)   # 40% of badge width max
        max_logo_height = int(scale_width * 0.20)  # 20% of badge width max

        # Make RT audience logos bigger (popcorn has more negative space)
        if source == 'rt_audience':
            # Spilled popcorn (rotten) needs to be bigger, standing (fresh) slightly bigger
            if logo_key == 'rt_audience_rotten':
                max_logo_width = int(max_logo_width * 1.3)
                max_logo_height = int(max_logo_height * 1.3)
            else:  # rt_audience_fresh
                max_logo_width = int(max_logo_width * 1.2)
                max_logo_height = int(max_logo_height * 1.2)

        if logo:
            # Calculate resize keeping aspect ratio
            orig_width, orig_height = logo.size
            aspect_ratio = orig_width / orig_height

            # Fit within max dimensions while maintaining aspect ratio
            if aspect_ratio > (max_logo_width / max_logo_height):
                # Width is the limiting factor
                logo_width = max_logo_width
                logo_height = int(max_logo_width / aspect_ratio)
            else:
                # Height is the limiting factor
                logo_height = max_logo_height
                logo_width = int(max_logo_height * aspect_ratio)

            # Resize logo maintaining aspect ratio
            logo_resized = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)

            # Left-align all logos for consistency (only center vertically)
            logo_x = x_padding
            logo_y = y_offset + (row_height - logo_height) // 2

            # Paste logo (use logo as mask for transparency)
            badge.paste(logo_resized, (logo_x, logo_y), logo_resized)
        else:
            # Fallback: draw source name if no logo
            self._draw_text_with_shadow(
                draw,
                (x_padding, y_offset + row_height // 2),
                source.upper(),
                font_small,
                (255, 255, 255, 255)
            )

        # Draw rating score with drop shadow (no background!)
        # Scale shadow based on badge width
        shadow_large = int(scale_width * 0.01)  # 1% of width
        shadow_small = int(scale_width * 0.005)  # 0.5% of width

        if source in ['rt', 'rt_critic', 'rt_audience']:
            # Rotten Tomatoes is percentage - split number and % symbol
            rating_number = f"{int(rating)}"
            percent_symbol = "%"

            # Position to align with TMDB/IMDb scores
            rating_x = int(badge_width * 0.80)  # 80% across badge for better alignment
            rating_y = y_offset + (row_height // 2)

            # Get text sizes for alignment
            number_bbox = draw.textbbox((0, 0), rating_number, font=font_large)
            percent_bbox = draw.textbbox((0, 0), percent_symbol, font=font_small)

            total_width = (number_bbox[2] - number_bbox[0]) + (percent_bbox[2] - percent_bbox[0]) + int(scale_width * 0.01)

            # Draw rating number with shadow (GOLD text, large)
            self._draw_text_with_shadow(
                draw,
                (rating_x - total_width, rating_y),
                rating_number,
                font_large,
                rating_color,  # Custom rating color
                shadow_offset=shadow_large,
                anchor="lm"
            )

            # Draw % symbol with shadow (WHITE text, small)
            self._draw_text_with_shadow(
                draw,
                (rating_x - (percent_bbox[2] - percent_bbox[0]), rating_y + int(scale_width * 0.02)),
                percent_symbol,
                font_small,
                (255, 255, 255, 255),  # White
                shadow_offset=shadow_small,
                anchor="lm"
            )
        else:
            # TMDB and IMDb - just show the number (cleaner design)
            rating_text = f"{rating:.1f}"

            # Position at right edge (align with RT percentages)
            rating_x = badge_width - x_padding
            rating_y = y_offset + (row_height // 2)

            # Get text size for right alignment
            rating_bbox = draw.textbbox((0, 0), rating_text, font=font_large)
            text_width = rating_bbox[2] - rating_bbox[0]

            # Draw rating number with shadow (GOLD text) - right aligned
            self._draw_text_with_shadow(
                draw,
                (rating_x - text_width, rating_y),
                rating_text,
                font_large,
                rating_color,  # Custom rating color
                shadow_offset=shadow_large,
                anchor="lm"
            )

    def apply_to_poster(
        self,
        poster_path: str,
        ratings: Dict[str, float],
        output_path: str,
        position: str = 'northeast',
        badge_style: Optional[Dict[str, Any]] = None,
        badge_positions: Optional[Dict[str, Dict[str, float]]] = None
    ) -> Image.Image:
        """
        Apply rating badge(s) to poster

        Supports two modes:
        1. Unified badge mode (legacy): Single badge with all ratings
        2. Individual badge mode (new): Separate badge for each rating source

        Args:
            poster_path: Path to poster image
            ratings: Dict of ratings {'tmdb': 7.2, 'imdb': 7.5, 'rt_critic': 85, 'rt_audience': 92}
            output_path: Output path
            position: Badge position for unified mode (legacy)
            badge_style: Optional styling options
            badge_positions: Optional dict for individual mode. Format:
                            {'tmdb': {'x': 5, 'y': 5}, 'imdb': {'x': 20, 'y': 5}, ...}
                            If source key exists, that badge is enabled at that position.
                            X/Y are percentages (0-100) of poster dimensions.

        Returns:
            PIL Image
        """
        # Open poster
        poster = Image.open(poster_path).convert('RGBA')
        poster_width, poster_height = poster.size

        # MODE 1: Individual badges (new 4-badge system)
        if badge_positions:
            for source, rating in ratings.items():
                # Check if this source is enabled (key exists in badge_positions)
                if source not in badge_positions:
                    continue

                pos = badge_positions[source]
                x_percent = pos.get('x', 5)
                y_percent = pos.get('y', 5)

                # Create individual badge
                badge = self.create_individual_badge(
                    source=source,
                    rating=rating,
                    poster_size=(poster_width, poster_height),
                    badge_style=badge_style
                )

                # Convert percentage to pixels
                badge_x = int((x_percent / 100) * poster_width)
                badge_y = int((y_percent / 100) * poster_height)

                # Composite badge onto poster
                poster.paste(badge, (badge_x, badge_y), badge)

            # Save
            poster_rgb = poster.convert('RGB')
            poster_rgb.save(output_path, 'JPEG', quality=95)

            enabled_sources = ', '.join([f'{k.upper()}: {v}' for k, v in ratings.items() if k in badge_positions])
            print(f"✓ Applied individual rating badges: {output_path}")
            print(f"  Enabled badges: {enabled_sources}")

            return poster

        # MODE 2: Unified badge (legacy - backward compatible)
        else:
            # Create unified badge with all ratings
            badge = self.create_multi_rating_badge(
                ratings=ratings,
                poster_size=(poster_width, poster_height),
                position=position,
                badge_style=badge_style
            )

            badge_width, badge_height = badge.size

            # Calculate position - small offset from edges
            offset_x = int(poster_width * 0.02)  # 2% from edges (close to edge)
            offset_y = int(poster_height * 0.02)

            positions = {
                'northeast': (poster_width - badge_width - offset_x, offset_y),
                'northwest': (offset_x, offset_y),
                'southeast': (poster_width - badge_width - offset_x, poster_height - badge_height - offset_y),
                'southwest': (offset_x, poster_height - badge_height - offset_y)
            }

            badge_x, badge_y = positions.get(position, positions['northeast'])

            # Composite badge onto poster
            poster.paste(badge, (badge_x, badge_y), badge)

            # Save
            poster_rgb = poster.convert('RGB')
            poster_rgb.save(output_path, 'JPEG', quality=95)

            print(f"✓ Applied multi-rating overlay: {output_path}")
            print(f"  Position: {position} ({badge_x}, {badge_y})")
            print(f"  Ratings: {', '.join([f'{k.upper()}: {v}' for k, v in ratings.items()])}")

            return poster
