import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import Base

class WatchlistItem(Base):
    __tablename__ = "watchlist_item"
    __table_args__ = (
        UniqueConstraint("device_id", "media_item_id", name="uq_watchlist_item_device_media"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(String, nullable=False)
    media_item_id = Column(UUID(as_uuid=True), ForeignKey("media_item.id"), nullable=False)
    watched = Column(Boolean, default=False)
    watched_at = Column(DateTime(timezone=True), nullable=True)
    added_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    media_item = relationship("MediaItem")
