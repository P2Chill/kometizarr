#!/usr/bin/env python3
"""
Demo: Generate rating badges without API calls
"""

from PIL import Image, ImageDraw, ImageFont
import sys

def create_rating_badge(rating, output_path='rating_badge.png', style='default'):
    """Create a rating badge with different styles"""

    # Badge dimensions
    width, height = 300, 120

    # Create transparent image
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Style configurations
    styles = {
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

    config = styles.get(style, styles['default'])

    # Background rounded rectangle
    padding = 10
    draw.rounded_rectangle(
        [(padding, padding), (width-padding, height-padding)],
        radius=config['radius'],
        fill=config['bg_color']
    )

    # Load fonts
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
    except:
        print("Warning: Could not load fonts, using default")
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Draw star
    star_text = "⭐"
    star_bbox = draw.textbbox((0, 0), star_text, font=font_large)
    star_x = 30
    star_y = (height - (star_bbox[3] - star_bbox[1])) // 2
    draw.text((star_x, star_y), star_text, font=font_large, fill=config['star_color'])

    # Draw rating
    rating_text = f"{rating:.1f}"
    star_width = star_bbox[2] - star_bbox[0]
    rating_bbox = draw.textbbox((0, 0), rating_text, font=font_large)
    rating_x = star_x + star_width + 10
    rating_y = (height - (rating_bbox[3] - rating_bbox[1])) // 2
    draw.text((rating_x, rating_y), rating_text, font=font_large, fill=config['text_color'])

    # Draw /10
    subscript_text = "/10"
    rating_width = rating_bbox[2] - rating_bbox[0]
    subscript_x = rating_x + rating_width + 5
    subscript_y = rating_y + 20
    draw.text((subscript_x, subscript_y), subscript_text, font=font_small, fill=config['text_color'])

    # Save
    img.save(output_path)
    print(f"✓ Created {style} badge: {output_path}")

    return img


def main():
    print("=== Rating Badge Generator Demo ===\n")

    # Generate different styles
    ratings = [
        (8.5, 'default'),
        (7.8, 'imdb'),
        (9.2, 'rt_fresh'),
        (6.4, 'minimal')
    ]

    for rating, style in ratings:
        output = f"/tmp/badge_{style}_{rating}.png"
        create_rating_badge(rating, output, style)

    print("\n✓ Generated 4 sample badges in /tmp/")
    print("\nBadge styles:")
    print("  - default: Black background, white text, gold star")
    print("  - imdb: Yellow background (IMDb colors)")
    print("  - rt_fresh: Red background (Rotten Tomatoes)")
    print("  - minimal: Dark background, yellow star")
    print("\nCheck /tmp/badge_*.png to see results!")


if __name__ == '__main__':
    main()
