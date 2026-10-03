from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class PushNotificationProvider(ABC):
    @abstractmethod
    async def send(
        self,
        push_token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        image_url: Optional[str] = None
    ) -> bool:
        pass
