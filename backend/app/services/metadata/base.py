from abc import ABC, abstractmethod
from typing import Optional, List
from app.schemas.search import SearchResult
from app.schemas.media import MediaItemSchema

class MetadataProvider(ABC):
    @abstractmethod
    async def search(self, query: str, media_type: str = "all", page: int = 1, limit: int = 10):
        pass
    
    @abstractmethod
    async def get_details(self, provider_id: str, media_type: str) -> Optional[MediaItemSchema]:
        pass
