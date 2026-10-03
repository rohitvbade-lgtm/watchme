import pytest
from httpx import AsyncClient
from unittest.mock import patch
from app.schemas.search import SearchResult

@pytest.mark.asyncio
async def test_search_returns_normalized_results(client: AsyncClient):
    with patch("app.services.metadata.tmdb.TMDBMetadataProvider.search") as mock_search:
        mock_search.return_value = [
            SearchResult(
                providerId="123",
                mediaType="movie",
                title="Mock Movie",
                originalTitle="Mock Movie",
                overview="A mock movie",
                genres=[]
            )
        ]
        response = await client.get("/api/search?q=mock&type=movie")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["results"][0]["title"] == "Mock Movie"

@pytest.mark.asyncio
async def test_search_empty_query(client: AsyncClient):
    response = await client.get("/api/search?q=")
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_search_tmdb_error_graceful(client: AsyncClient):
    with patch("app.services.metadata.tmdb.TMDBMetadataProvider.search") as mock_search:
        mock_search.return_value = []
        response = await client.get("/api/search?q=error")
        assert response.status_code == 200
        assert response.json()["total"] == 0

@pytest.mark.asyncio
async def test_search_media_type_filtering(client: AsyncClient):
    response = await client.get("/api/search?q=mock&type=invalid")
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_search_pagination(client: AsyncClient):
    with patch("app.services.metadata.tmdb.TMDBMetadataProvider.search") as mock_search:
        # Mock returning 10 items out of 25 total
        mock_items = [
            SearchResult(
                providerId=str(i),
                mediaType="movie",
                title=f"Movie {i}",
                originalTitle=f"Movie {i}",
                overview=f"Overview {i}",
                genres=[]
            ) for i in range(10)
        ]
        mock_search.return_value = (mock_items, 25)

        response = await client.get("/api/search?q=movie&page=2&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 25
        assert data["page"] == 2
        assert data["limit"] == 10
        assert data["totalPages"] == 3
        assert len(data["results"]) == 10
