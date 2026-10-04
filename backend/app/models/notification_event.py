import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import Base

class NotificationEvent(Base):
    __tablename__ = "notification_event"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(String, nullable=False)
    watchlist_item_id = Column(UUID(as_uuid=True), ForeignKey("watchlist_item.id", ondelete="SET NULL"), nullable=True)
    item_title = Column(String, nullable=True)
    item_image_url = Column(String, nullable=True)
    text = Column(String, nullable=False)
    generation_method = Column(String, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    sent_at = Column(DateTime(timezone=True), nullable=True)

    watchlist_item = relationship("WatchlistItem", back_populates="notification_events")
