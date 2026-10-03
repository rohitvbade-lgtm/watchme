import httpx
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class WebSearchService:
    """
    Optional web search using DuckDuckGo Instant Answer API.
    No API key required. Returns empty list on any failure.
    Used to enrich notification context with current information.
    """

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=5.0,
            headers={"User-Agent": "WatchMe-App/1.0 (watchlist notification enrichment)"},
            follow_redirects=True,
        )

    async def search(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """
        Search using DuckDuckGo Instant Answer JSON API.
        Returns list of {title, url, snippet} dicts, or [] on failure.
        """
        results = []
        try:
            response = await self.client.get(
                "https://api.duckduckgo.com/",
                params={"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"},
            )
            response.raise_for_status()
            data = response.json()

            # Abstract result (primary answer)
            if data.get("AbstractText") and data.get("AbstractURL"):
                results.append({
                    "title": data.get("Heading", query),
                    "url": data.get("AbstractURL", ""),
                    "snippet": data["AbstractText"][:300],
                })

            # Related topics
            for topic in data.get("RelatedTopics", []):
                if len(results) >= max_results:
                    break
                if isinstance(topic, dict) and topic.get("Text"):
                    results.append({
                        "title": topic.get("Text", "")[:80],
                        "url": topic.get("FirstURL", ""),
                        "snippet": topic.get("Text", "")[:300],
                    })

        except Exception as e:
            logger.warning(f"Web search failed (non-critical): {e}")

        return results[:max_results]
