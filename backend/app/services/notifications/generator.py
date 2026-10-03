from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple

class NotificationGenerator(ABC):
    @abstractmethod
    async def generate(self, media_item: Dict[str, Any]) -> Tuple[str, str]:
        """Returns (notification_text, generation_method)"""
        pass
