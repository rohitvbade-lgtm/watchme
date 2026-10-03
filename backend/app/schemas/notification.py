from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID

class NotificationEventSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    deviceId: str
    watchlistItemId: Optional[UUID] = None
    itemTitle: Optional[str] = None
    itemImageUrl: Optional[str] = None
    text: str
    generationMethod: str
    status: str
    createdAt: datetime
    sentAt: Optional[datetime] = None

class DeviceRegisterRequest(BaseModel):
    deviceId: str
    platform: str
    pushToken: Optional[str] = None
