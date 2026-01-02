"""
Rating Fetcher - Fetch ratings from TMDB, TVDB, and OMDb APIs

Based on prototype_rating_overlay.py
MIT License - Copyright (c) 2026 Kometizarr Contributors
"""

import requests
from typing import Dict, Optional


class RatingFetcher:
    """Fetch ratings from multiple sources"""

    TMDB_BASE_URL = "https://api.themoviedb.org/3"
    OMDB_BASE_URL = "http://www.omdbapi.com/"
    MDBLIST_BASE_URL = "https://mdblist.com/api"

    def __init__(self, tmdb_api_key: str, omdb_api_key: Optional[str] = None, mdblist_api_key: Optional[str] = None):
        """
        Initialize rating fetcher

        Args:
            tmdb_api_key: TMDB API key (required)
            omdb_api_key: OMDb API key (optional, for IMDb/RT ratings)
            mdblist_api_key: MDBList API key (optional, for RT audience scores)
        """
        self.tmdb_api_key = tmdb_api_key
        self.omdb_api_key = omdb_api_key
        self.mdblist_api_key = mdblist_api_key

    def fetch_tmdb_rating(self, tmdb_id: int, media_type: str = 'movie') -> Optional[Dict]:
        """
        Fetch TMDB rating for a movie or TV show

        Args:
            tmdb_id: TMDB ID
            media_type: 'movie' or 'tv'

        Returns:
            Dict with rating, vote_count, and title, or None if error
        """
        endpoint = f"{media_type}/{tmdb_id}"
        url = f"{self.TMDB_BASE_URL}/{endpoint}?api_key={self.tmdb_api_key}"

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            rating = data.get('vote_average', 0)
            vote_count = data.get('vote_count', 0)
            title = data.get('title') if media_type == 'movie' else data.get('name')

            return {
                'rating': rating,
                'vote_count': vote_count,
                'title': title,
                'source': 'tmdb'
            }
        except Exception as e:
            print(f"✗ Error fetching TMDB rating: {e}")
            return None

    def fetch_tmdb_episode_rating(self, tmdb_id: int, season: int, episode: int) -> Optional[Dict]:
        """
        Fetch TMDB rating for a specific TV episode

        Args:
            tmdb_id: TMDB TV show ID
            season: Season number
            episode: Episode number

        Returns:
            Dict with rating and vote_count, or None if error
        """
        url = f"{self.TMDB_BASE_URL}/tv/{tmdb_id}/season/{season}/episode/{episode}?api_key={self.tmdb_api_key}"

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            return {
                'rating': data.get('vote_average', 0),
                'vote_count': data.get('vote_count', 0),
                'episode_name': data.get('name'),
                'source': 'tmdb'
            }
        except Exception as e:
            print(f"✗ Error fetching episode rating: {e}")
            return None

    def fetch_omdb_rating(self, imdb_id: str) -> Optional[Dict]:
        """
        Fetch IMDb and Rotten Tomatoes ratings from OMDb

        Args:
            imdb_id: IMDb ID (e.g., 'tt0111161')

        Returns:
            Dict with imdb_rating, rt_audience, rt_critic, or None if error
        """
        if not self.omdb_api_key:
            print("⚠️  OMDb API key not configured")
            return None

        url = f"{self.OMDB_BASE_URL}?i={imdb_id}&apikey={self.omdb_api_key}"

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            if data.get('Response') == 'False':
                print(f"✗ OMDb error: {data.get('Error')}")
                return None

            # Parse ratings
            result = {
                'imdb_rating': data.get('imdbRating'),
                'imdb_votes': data.get('imdbVotes'),
                'source': 'omdb'
            }

            # Parse RT ratings from Ratings array
            for rating in data.get('Ratings', []):
                if rating['Source'] == 'Rotten Tomatoes':
                    result['rt_score'] = rating['Value']  # e.g., "95%"
                elif rating['Source'] == 'Metacritic':
                    result['metacritic'] = rating['Value']  # e.g., "80/100"

            return result
        except Exception as e:
            print(f"✗ Error fetching OMDb rating: {e}")
            return None

    def fetch_mdblist_rating(self, imdb_id: str) -> Optional[Dict]:
        """
        Fetch RT ratings from MDBList (includes both critic and audience scores)

        Args:
            imdb_id: IMDb ID (e.g., 'tt0111161')

        Returns:
            Dict with rt_critic, rt_audience scores, or None if error
        """
        if not self.mdblist_api_key:
            print("⚠️  MDBList API key not configured")
            return None

        url = f"{self.MDBLIST_BASE_URL}/?apikey={self.mdblist_api_key}&i={imdb_id}"

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            result = {}

            # MDBList returns ratings in format like: ratings[0].source = "tomatoes", ratings[0].value = 85
            ratings_data = data.get('ratings', [])

            for rating in ratings_data:
                source = rating.get('source', '').lower()
                value = rating.get('value')

                if source == 'tomatoes' and value:
                    result['rt_critic'] = float(value)
                elif source == 'tomatoesaudience' and value:
                    result['rt_audience'] = float(value)

            return result if result else None

        except Exception as e:
            print(f"✗ Error fetching MDBList rating: {e}")
            return None
