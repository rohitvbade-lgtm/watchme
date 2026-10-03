import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Date, Integer, Float, Boolean, JSON, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.models.base import Base

class MediaItem(Base):
    __tablename__ = "media_item"
    __table_args__ = (
        UniqueConstraint("provider", "provider_id", "media_type", name="uq_media_item_provider_id_type"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider = Column(String, nullable=False)
    provider_id = Column(String, nullable=False)
    media_type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    original_title = Column(String, nullable=True)
    overview = Column(String, nullable=True)
    poster_path = Column(String, nullable=True)
    backdrop_path = Column(String, nullable=True)
    release_date = Column(Date, nullable=True)
    first_air_date = Column(Date, nullable=True)
    runtime = Column(Integer, nullable=True)
    genres_json = Column(JSON, nullable=True)
    metadata_json = Column(JSONB, nullable=True)
    rating = Column(Float, nullable=True)
    vote_count = Column(Integer, nullable=True)
    popularity = Column(Float, nullable=True)
    original_language = Column(String, nullable=True)
    adult = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
