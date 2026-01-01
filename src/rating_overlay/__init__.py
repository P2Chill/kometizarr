"""
Rating Overlay Module for Kometizarr

Provides functionality to fetch ratings from various APIs and generate
dynamic rating badges for movie/TV show posters.
"""

from .rating_fetcher import RatingFetcher
from .badge_generator import BadgeGenerator
from .overlay_composer import OverlayComposer

__all__ = ['RatingFetcher', 'BadgeGenerator', 'OverlayComposer']
