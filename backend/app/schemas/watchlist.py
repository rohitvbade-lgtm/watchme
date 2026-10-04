from pydantic import BaseModel, ConfigDict, Field, AliasChoices, computed_field
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from .media import MediaItemSchema


class WatchlistAddRequest(BaseModel):
    provider: str
    providerId: str
    mediaType: str


class WatchlistItemSchema(BaseModel):
    """
    Response schema for watchlist items.
    Uses camelCase field names (matching frontend TypeScript interfaces)
    while also providing snake_case computed fields for maximum compatibility.
    """
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    deviceId: str = Field(default="", validation_alias=AliasChoices("device_id", "deviceId"))
    mediaItem: Optional[MediaItemSchema] = Field(default=None, validation_alias=AliasChoices("media_item", "mediaItem"))
    watched: bool = False
    watchedAt: Optional[datetime] = Field(default=None, validation_alias=AliasChoices("watched_at", "watchedAt"))
    rewatch: bool = False
    addedAt: Optional[datetime] = Field(default=None, validation_alias=AliasChoices("added_at", "addedAt"))

    @computed_field
    @property
    def media_item(self) -> Optional[MediaItemSchema]:
        return self.mediaItem

    @computed_field
    @property
    def device_id(self) -> str:
        return self.deviceId

    @computed_field
    @property
    def watched_at(self) -> Optional[datetime]:
        return self.watchedAt

    @computed_field
    @property
    def added_at(self) -> Optional[datetime]:
        return self.addedAt

    @classmethod
    def from_orm_item(cls, item: object) -> "WatchlistItemSchema":
        """Build schema from SQLAlchemy ORM WatchlistItem (with media_item loaded)."""
        return cls(
            id=item.id,
            device_id=item.device_id,
            media_item=item.media_item,
            watched=bool(item.watched),
            watched_at=item.watched_at,
            rewatch=bool(item.rewatch) if item.rewatch is not None else False,
            added_at=item.added_at,
        )

    def model_dump_json_safe(self) -> dict:
        """Dump with field names (camelCase) for JSON responses."""
        return self.model_dump(by_alias=False)


class WatchlistResponse(BaseModel):
    items: List[WatchlistItemSchema]
    total: int = 0
    page: int = 1
    totalPages: int = 1
    limit: int = 10
