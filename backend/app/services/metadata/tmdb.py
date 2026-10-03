import httpx
import logging
from typing import List, Optional, Dict, Any
from app.services.metadata.base import MetadataProvider
from app.schemas.search import SearchResult
from app.schemas.media import MediaItemSchema
from app.config import get_settings
import uuid
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class TMDBMetadataProvider(MetadataProvider):
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.tmdb_api_key
        self.base_url = settings.tmdb_base_url.rstrip("/")
        self.image_base_url = settings.tmdb_image_base_url
        self.client = httpx.AsyncClient(timeout=10.0)

    async def _fetch(self, path: str, params: dict) -> dict:
        """
        Fetch JSON from TMDB API with browser-like headers, sensible timeout,
        and automatic fallback between api.tmdb.org and api.themoviedb.org.
        """
        headers = {
            "User-Agent": "WatchMeApp/1.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "application/json"
        }
        query_params = {"api_key": self.api_key, **params}

        # Build candidate base URLs (primary configured first, then official fallback mirror)
        candidate_bases = [self.base_url]
        if "api.tmdb.org" not in self.base_url:
            candidate_bases.append("https://api.tmdb.org/3")
        if "api.themoviedb.org" not in self.base_url:
            candidate_bases.append("https://api.themoviedb.org/3")

        last_exc = None
        for base in candidate_bases:
            endpoint = f"{base}/{path.lstrip('/')}"
            try:
                async with httpx.AsyncClient(headers=headers, timeout=10.0, follow_redirects=True) as client:
                    resp = await client.get(endpoint, params=query_params)
                    resp.raise_for_status()
                    return resp.json()
            except Exception as e:
                last_exc = e
                logger.warning(f"TMDB request to {endpoint} failed ({type(e).__name__}: {e!r}). Trying fallback...")

        raise last_exc or RuntimeError("All TMDB endpoints failed")

    async def search(self, query: str, media_type: str = "all", page: int = 1, limit: int = 10):
        if not self.api_key:
            logger.warning("TMDB API key is missing. Returning empty search results.")
            return ([], 0)

        # TMDB returns 20 items per page.
        tmdb_page = ((page - 1) * limit) // 20 + 1
        offset = ((page - 1) * limit) % 20

        path = "search/multi" if media_type == "all" else f"search/{media_type}"
        params = {"query": query, "page": tmdb_page}
        
        try:
            data = await self._fetch(path, params)
        except Exception as e:
            logger.error(f"TMDB search failed: {type(e).__name__}: {e!r}")
            return ([], 0)

        raw_items = data.get("results", [])
        total_results = data.get("total_results", len(raw_items))

        # Filter valid items
        valid_items = [
            item for item in raw_items
            if item.get("media_type", media_type) in ("movie", "tv")
        ]

        # Slice for the requested page and limit
        paged_slice = valid_items[offset : offset + limit] if offset < len(valid_items) else []

        results = []
        for item in paged_slice:
            m_type = item.get("media_type", media_type)
            poster_path = item.get("poster_path")
            poster_url = f"{self.image_base_url}{poster_path}" if poster_path else None
            
            title = item.get("title") or item.get("name") or "Unknown"
            original_title = item.get("original_title") or item.get("original_name") or title
            release_date = item.get("release_date") or item.get("first_air_date")
            
            results.append(SearchResult(
                providerId=str(item.get("id")),
                mediaType=m_type,
                title=title,
                originalTitle=original_title,
                releaseDate=release_date,
                posterUrl=poster_url,
                overview=item.get("overview", ""),
                genres=[]
            ))

        return (results, total_results)

    async def get_details(self, provider_id: str, media_type: str) -> Optional[MediaItemSchema]:
        if not self.api_key:
            return None

        path = f"{media_type}/{provider_id}"
        
        try:
            data = await self._fetch(path, {})
        except Exception as e:
            logger.error(f"TMDB get_details failed: {type(e).__name__}: {e!r}")
            return None
            
        title = data.get("title") or data.get("name") or "Unknown"
        original_title = data.get("original_title") or data.get("original_name") or title
        
        release_date = data.get("release_date")
        first_air_date = data.get("first_air_date")
        
        def parse_date(d_str: str) -> Optional[datetime]:
            if not d_str: return None
            try: return datetime.strptime(d_str, "%Y-%m-%d").date()
            except ValueError: return None
            
        metadata_json = {}
        if media_type == "tv":
            metadata_json["numberOfSeasons"] = data.get("number_of_seasons")
            metadata_json["numberOfEpisodes"] = data.get("number_of_episodes")
            metadata_json["networks"] = data.get("networks", [])
            metadata_json["nextEpisode"] = data.get("next_episode_to_air")
        elif media_type == "movie":
            metadata_json["runtime"] = data.get("runtime")
            metadata_json["production_companies"] = data.get("production_companies", [])
            
        return MediaItemSchema(
            id=uuid.uuid4(),
            provider="tmdb",
            provider_id=str(data.get("id")),
            media_type=media_type,
            title=title,
            original_title=original_title,
            overview=data.get("overview"),
            poster_path=data.get("poster_path"),
            backdrop_path=data.get("backdrop_path"),
            release_date=parse_date(release_date),
            first_air_date=parse_date(first_air_date),
            runtime=data.get("runtime") if media_type == "movie" else None,
            genres_json=data.get("genres", []),
            metadata_json=metadata_json,
            rating=data.get("vote_average"),
            vote_count=data.get("vote_count"),
            popularity=data.get("popularity"),
            original_language=data.get("original_language"),
            adult=data.get("adult", False),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
