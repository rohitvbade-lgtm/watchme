import pytest
from httpx import AsyncClient
from unittest.mock import patch
from app.schemas.media import MediaItemSchema
from datetime import datetime, timezone
import uuid

mock_media = MediaItemSchema(
    id=uuid.uuid4(), provider="tmdb", provider_id="123", media_type="movie",
    title="Mock", created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
)

@pytest.mark.asyncio
async def test_watchlist_flow(client: AsyncClient):
    with patch("app.services.metadata.tmdb.TMDBMetadataProvider.get_details") as mock_details:
        mock_details.return_value = mock_media
        
        # Add item
        resp1 = await client.post("/api/watchlist?device_id=dev1", json={
            "provider": "tmdb", "providerId": "123", "mediaType": "movie"
        })
        assert resp1.status_code == 200
        item_id = resp1.json()["id"]
        
        # Add duplicate
        resp2 = await client.post("/api/watchlist?device_id=dev1", json={
            "provider": "tmdb", "providerId": "123", "mediaType": "movie"
        })
        assert resp2.status_code == 409
        
        # Get watchlist
        resp3 = await client.get("/api/watchlist?device_id=dev1")
        assert resp3.status_code == 200
        assert len(resp3.json()["items"]) == 1
        
        # Mark watched
        resp4 = await client.post(f"/api/watchlist/{item_id}/watched?device_id=dev1")
        assert resp4.status_code == 200
        assert resp4.json()["watched"] == True
        
        # Mark unwatched
        resp5 = await client.post(f"/api/watchlist/{item_id}/unwatched?device_id=dev1")
        assert resp5.status_code == 200
        assert resp5.json()["watched"] == False
        
        # Delete
        resp6 = await client.delete(f"/api/watchlist/{item_id}?device_id=dev1")
        assert resp6.status_code == 200
        
        # Verify empty
        resp7 = await client.get("/api/watchlist?device_id=dev1")
        assert len(resp7.json()["items"]) == 0


@pytest.mark.asyncio
async def test_watchlist_pagination(client: AsyncClient):
    with patch("app.services.metadata.tmdb.TMDBMetadataProvider.get_details") as mock_details:
        # Add 12 items for dev_page
        for i in range(12):
            media = MediaItemSchema(
                id=uuid.uuid4(), provider="tmdb", provider_id=f"page_item_{i}", media_type="movie",
                title=f"Movie {i}", created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
            )
            mock_details.return_value = media
            resp = await client.post("/api/watchlist?device_id=dev_page", json={
                "provider": "tmdb", "providerId": f"page_item_{i}", "mediaType": "movie"
            })
            assert resp.status_code == 200

        # Page 1 (limit 10)
        p1 = await client.get("/api/watchlist?device_id=dev_page&page=1&limit=10")
        assert p1.status_code == 200
        p1_data = p1.json()
        assert p1_data["total"] == 12
        assert p1_data["totalPages"] == 2
        assert len(p1_data["items"]) == 10
        assert p1_data["page"] == 1
        # Check camelCase and snake_case both present
        assert "mediaItem" in p1_data["items"][0]
        assert "media_item" in p1_data["items"][0]

        # Page 2 (limit 10)
        p2 = await client.get("/api/watchlist?device_id=dev_page&page=2&limit=10")
        assert p2.status_code == 200
        p2_data = p2.json()
        assert len(p2_data["items"]) == 2
        assert p2_data["page"] == 2

        # all_items=True for sync
        sync_resp = await client.get("/api/watchlist?device_id=dev_page&all_items=true")
        assert sync_resp.status_code == 200
        assert len(sync_resp.json()["items"]) == 12
