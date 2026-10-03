import pytest
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient

from app.models.media_item import MediaItem
from app.models.watchlist_item import WatchlistItem
from app.models.notification_event import NotificationEvent
from app.services.notifications.template_generator import TemplateNotificationGenerator
from app.services.notifications.ai_generator import AINotificationGenerator
from app.services.notifications.candidate_service import NotificationCandidateService

@pytest.mark.asyncio
async def test_template_generator():
    gen = TemplateNotificationGenerator()
    
    # Test sci-fi
    text_scifi, method = await gen.generate({"title": "Interstellar", "genres": [{"name": "Science Fiction"}], "media_type": "movie"})
    assert "Interstellar" in text_scifi
    assert method == "template"
    
    # Test action
    text_action, _ = await gen.generate({"title": "Spider-Man", "genres": [{"name": "Action"}], "media_type": "movie"})
    assert "Spider-Man" in text_action
    
    # Test TV
    text_tv, _ = await gen.generate({"title": "Breaking Bad", "genres": [{"name": "Crime"}], "media_type": "tv"})
    assert "Breaking Bad" in text_tv

@pytest.mark.asyncio
async def test_ai_generator_fallback():
    gen = AINotificationGenerator()
    gen.client = MagicMock()
    gen.client.chat.completions.create.side_effect = Exception("Groq Rate Limit")
    
    with pytest.raises(Exception):
        await gen.generate({"title": "Matrix"})

@pytest.mark.asyncio
async def test_candidate_service_empty(db: AsyncSession):
    svc = NotificationCandidateService()
    candidate = await svc.select_candidate(db, "dev_empty")
    assert candidate is None

@pytest.mark.asyncio
async def test_candidate_service_selection_and_cooldown(db: AsyncSession):
    svc = NotificationCandidateService()
    device_id = "dev_candidate_test"
    
    # Create media item and watchlist item
    media = MediaItem(
        id=uuid.uuid4(),
        provider="tmdb",
        provider_id="101",
        media_type="movie",
        title="Inception",
        genres_json=[{"id": 1, "name": "Sci-Fi"}]
    )
    db.add(media)
    await db.flush()
    
    watchlist_item = WatchlistItem(
        id=uuid.uuid4(),
        device_id=device_id,
        media_item_id=media.id,
        watched=False
    )
    db.add(watchlist_item)
    await db.commit()
    
    # 1. Selection succeeds when no notifications sent recently
    selected = await svc.select_candidate(db, device_id)
    assert selected is not None
    assert selected.id == watchlist_item.id
    assert selected.media_item.title == "Inception"
    
    # 2. Record a notification sent within the last 24h
    event = NotificationEvent(
        id=uuid.uuid4(),
        device_id=device_id,
        watchlist_item_id=watchlist_item.id,
        text="Feeling like a sci-fi night?",
        generation_method="template",
        status="SENT",
        sent_at=datetime.now(timezone.utc) - timedelta(hours=2)
    )
    db.add(event)
    await db.commit()
    
    # 3. Item is now cooled down and excluded from candidates
    cooled_down = await svc.select_candidate(db, device_id)
    assert cooled_down is None

@pytest.mark.asyncio
async def test_candidate_service_rewatch_eligibility(db: AsyncSession):
    """Verifies that rewatched items remain eligible for notification selection."""
    svc = NotificationCandidateService()
    device_id = "dev_rewatch_test"
    
    media = MediaItem(
        id=uuid.uuid4(),
        provider="tmdb",
        provider_id="202",
        media_type="movie",
        title="Spirited Away",
        genres_json=[{"id": 16, "name": "Animation"}]
    )
    db.add(media)
    await db.flush()
    
    # Watched item (rewatch case)
    watchlist_item = WatchlistItem(
        id=uuid.uuid4(),
        device_id=device_id,
        media_item_id=media.id,
        watched=True,
        watched_at=datetime.now(timezone.utc) - timedelta(days=7)
    )
    db.add(watchlist_item)
    await db.commit()
    
    # Watched item should STILL be eligible (not permanently suppressed)
    selected = await svc.select_candidate(db, device_id)
    assert selected is not None
    assert selected.id == watchlist_item.id

@pytest.mark.asyncio
async def test_ai_generator_success():
    gen = AINotificationGenerator()
    mock_choice = MagicMock()
    mock_choice.message.content = "Don't miss this thrilling sci-fi adventure!"
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    
    gen.client = MagicMock()
    gen.client.chat.completions.create = MagicMock()
    
    async def mock_create(**kwargs):
        return mock_response
    
    gen.client.chat.completions.create.side_effect = mock_create
    
    text, method = await gen.generate({
        "title": "Interstellar",
        "overview": "A team of explorers travel through a wormhole in space.",
        "media_type": "movie"
    })
    assert "thrilling sci-fi" in text
    assert method == "ai"

@pytest.mark.asyncio
async def test_fcm_provider_simulated():
    from app.services.push.fcm import FCMPushProvider
    provider = FCMPushProvider()
    provider._initialized = True
    provider._has_credentials = False
    
    sent = await provider.send("fake_token_12345", "Test Title", "Test Body")
    assert sent is False

@pytest.mark.asyncio
async def test_fcm_provider_path_resolution():
    from app.services.push.fcm import FCMPushProvider
    resolved = FCMPushProvider._resolve_credentials_path("/watchme-166bb-firebase-adminsdk-fbsvc-66bfeccd20.json")
    assert resolved is not None
    assert "watchme-166bb-firebase-adminsdk-fbsvc-66bfeccd20.json" in resolved

@pytest.mark.asyncio
async def test_fcm_provider_image_support():
    from app.services.push.fcm import FCMPushProvider
    provider = FCMPushProvider()
    provider._initialized = True
    provider._has_credentials = False

    # Simulated token should succeed and accept image_url
    sent = await provider.send(
        "simulated_token_123",
        "Dune: Part Two",
        "The epic saga continues.",
        data={"url": "/item/123"},
        image_url="https://image.tmdb.org/t/p/w500/sample.jpg"
    )
    assert sent is True

@pytest.mark.asyncio
async def test_notification_api_includes_item_title_and_image(client: AsyncClient, db: AsyncSession):
    device_id = "dev_api_title_test"

    media = MediaItem(
        id=uuid.uuid4(),
        provider="tmdb",
        provider_id="999",
        media_type="movie",
        title="Dune: Part Two",
        poster_path="/dune2.jpg"
    )
    db.add(media)
    await db.flush()

    wl_item = WatchlistItem(
        id=uuid.uuid4(),
        device_id=device_id,
        media_item_id=media.id
    )
    db.add(wl_item)
    await db.flush()

    event = NotificationEvent(
        id=uuid.uuid4(),
        device_id=device_id,
        watchlist_item_id=wl_item.id,
        item_title="Dune: Part Two",
        item_image_url="https://image.tmdb.org/t/p/w500/dune2.jpg",
        text="Experience the sands of Arrakis!",
        generation_method="ai",
        status="SENT"
    )
    db.add(event)
    await db.commit()

    resp = await client.get(f"/api/notifications?device_id={device_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["itemTitle"] == "Dune: Part Two"
    assert data[0]["itemImageUrl"] == "https://image.tmdb.org/t/p/w500/dune2.jpg"
    assert data[0]["text"] == "Experience the sands of Arrakis!"

