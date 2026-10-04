from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from typing import List, Optional
import uuid
from datetime import datetime, timezone

from app.db.session import get_db
from app.schemas.notification import NotificationEventSchema
from app.models.notification_event import NotificationEvent
from app.models.watchlist_item import WatchlistItem
from app.config import get_settings

router = APIRouter()
settings = get_settings()

@router.get("", response_model=List[NotificationEventSchema])
async def get_notifications(device_id: str = Query(...), db: AsyncSession = Depends(get_db)):
    stmt = (
        select(NotificationEvent)
        .where(NotificationEvent.device_id == device_id)
        .options(selectinload(NotificationEvent.watchlist_item).selectinload(WatchlistItem.media_item))
        .order_by(desc(NotificationEvent.created_at))
        .limit(20)
    )
    
    result = await db.execute(stmt)
    events = result.scalars().all()
    
    out: List[NotificationEventSchema] = []
    for e in events:
        item_title = e.item_title
        item_image_url = e.item_image_url
        if (not item_title or not item_image_url) and e.watchlist_item and e.watchlist_item.media_item:
            if not item_title:
                item_title = e.watchlist_item.media_item.title
            if not item_image_url and e.watchlist_item.media_item.poster_path:
                p = e.watchlist_item.media_item.poster_path
                item_image_url = p if p.startswith("http") else f"{settings.tmdb_image_base_url}{p}"

        out.append(NotificationEventSchema(
            id=e.id,
            deviceId=e.device_id,
            watchlistItemId=e.watchlist_item_id,
            itemTitle=item_title,
            itemImageUrl=item_image_url,
            text=e.text,
            generationMethod=e.generation_method,
            status=e.status,
            createdAt=e.created_at,
            sentAt=e.sent_at
        ))
    return out

from pydantic import BaseModel
class TestNotifRequest(BaseModel):
    device_id: str
    watchlist_item_id: Optional[uuid.UUID] = None

@router.post("/test")
async def test_notification(req: TestNotifRequest, db: AsyncSession = Depends(get_db)):
    if not settings.debug:
        raise HTTPException(status_code=403, detail="Test endpoint only available in debug mode")

    from app.services.notifications.candidate_service import NotificationCandidateService
    from app.services.notifications.ai_generator import AINotificationGenerator
    from app.services.notifications.template_generator import TemplateNotificationGenerator
    from app.services.push.fcm import FCMPushProvider
    from app.models.device import Device

    candidate_service = NotificationCandidateService()
    ai_gen = AINotificationGenerator()
    template_gen = TemplateNotificationGenerator()
    push = FCMPushProvider()

    # Pick a specific item or let candidate service choose
    if req.watchlist_item_id:
        stmt = select(WatchlistItem).where(
            WatchlistItem.id == req.watchlist_item_id,
            WatchlistItem.device_id == req.device_id
        ).options(selectinload(WatchlistItem.media_item))
        result = await db.execute(stmt)
        candidate = result.scalar_one_or_none()
    else:
        candidate = await candidate_service.select_candidate(db, req.device_id)

    if not candidate:
        raise HTTPException(status_code=404, detail="No eligible watchlist item found for this device")

    item_title = candidate.media_item.title
    poster_path = candidate.media_item.poster_path
    image_url = None
    if poster_path:
        image_url = poster_path if poster_path.startswith("http") else f"{settings.tmdb_image_base_url}{poster_path}"

    media_item_dict = {
        "title": item_title,
        "overview": candidate.media_item.overview or "",
        "media_type": candidate.media_item.media_type,
        "genres": candidate.media_item.genres_json or [],
    }

    try:
        text, method = await ai_gen.generate(media_item_dict)
    except Exception as e:
        text, method = await template_gen.generate(media_item_dict)

    # Get push token for this device
    dev_stmt = select(Device).where(Device.device_id == req.device_id)
    dev_result = await db.execute(dev_stmt)
    device = dev_result.scalar_one_or_none()

    success = False
    if device and device.push_token:
        success = await push.send(
            push_token=device.push_token,
            title=item_title,
            body=text,
            image_url=image_url,
            data={
                "url": f"/item/{candidate.id}",
                "itemTitle": item_title,
                "imageUrl": image_url or ""
            }
        )

    event = NotificationEvent(
        device_id=req.device_id,
        watchlist_item_id=candidate.id,
        item_title=item_title,
        item_image_url=image_url,
        text=text,
        generation_method=method,
        status="SENT" if success else "GENERATED",
        sent_at=datetime.now(timezone.utc) if success else None
    )
    db.add(event)
    await db.commit()

    return {
        "status": "ok",
        "text": text,
        "itemTitle": item_title,
        "itemImageUrl": image_url,
        "method": method,
        "pushed": success
    }


