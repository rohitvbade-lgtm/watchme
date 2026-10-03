import pytest
from httpx import AsyncClient
from unittest.mock import patch
from app.schemas.media import MediaItemSchema
from datetime import datetime, timezone
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.media_item import MediaItem
from sqlalchemy import select

mock_media = MediaItemSchema(
    id=uuid.uuid4(), provider="tmdb", provider_id="999", media_type="movie",
    title="Cached", created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
)

@pytest.mark.asyncio
async def test_metadata_cache(client: AsyncClient, db: AsyncSession):
    with patch("app.services.metadata.tmdb.TMDBMetadataProvider.get_details") as mock_details:
        mock_details.return_value = mock_media
        
        # First call fetches from mock
        await client.post("/api/watchlist?device_id=dev1", json={
            "provider": "tmdb", "providerId": "999", "mediaType": "movie"
        })
        
        assert mock_details.call_count == 1
        
        # Verify in DB
        result = await db.execute(select(MediaItem).where(MediaItem.provider_id == "999"))
        assert result.scalar_one_or_none() is not None
        
        # Second call to same item different device shouldn't need get_details again
        # wait, the current implementation checks cache FIRST before calling TMDB.
        await client.post("/api/watchlist?device_id=dev2", json={
            "provider": "tmdb", "providerId": "999", "mediaType": "movie"
        })
        
        # Call count should still be 1
        assert mock_details.call_count == 1
