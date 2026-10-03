import random
from typing import Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.watchlist_item import WatchlistItem
from app.models.notification_event import NotificationEvent

class NotificationCandidateService:
    async def select_candidate(self, db: AsyncSession, device_id: str) -> Optional[WatchlistItem]:
        # 1. Fetch all watchlist items for device_id
        stmt = select(WatchlistItem).where(
            WatchlistItem.device_id == device_id
        ).options(selectinload(WatchlistItem.media_item))
        
        result = await db.execute(stmt)
        watchlist_items = result.scalars().all()
        
        if not watchlist_items:
            return None
            
        from app.config import get_settings
        settings = get_settings()

        if settings.debug:
            # In debug/dev mode, avoid only the single most recently notified item to ensure continuous rotation
            notif_stmt = (
                select(NotificationEvent.watchlist_item_id)
                .where(NotificationEvent.device_id == device_id)
                .order_by(NotificationEvent.created_at.desc())
                .limit(1)
            )
            notif_result = await db.execute(notif_stmt)
            recent_notified_id = notif_result.scalar_one_or_none()
            candidates = [item for item in watchlist_items if item.id != recent_notified_id]
            if not candidates:
                candidates = list(watchlist_items)
        else:
            # Production: Exclude items that had a notification sent in the last 24 hours
            twenty_four_hours_ago = datetime.now(timezone.utc) - timedelta(hours=24)
            notif_stmt = select(NotificationEvent.watchlist_item_id).where(
                NotificationEvent.device_id == device_id,
                NotificationEvent.sent_at >= twenty_four_hours_ago
            )
            notif_result = await db.execute(notif_stmt)
            recent_notified_ids = set(notif_result.scalars().all())
            candidates = [item for item in watchlist_items if item.id not in recent_notified_ids]
            if not candidates:
                return None
            
        # 3. Random weighted selection (unwatched weight 3, watched weight 1)
        weights = [1 if item.watched else 3 for item in candidates]
        
        selected = random.choices(candidates, weights=weights, k=1)[0]
        return selected
