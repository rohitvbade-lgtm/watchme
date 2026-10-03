from pydantic import BaseModel, ConfigDict
from typing import Optional, List

class SearchResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    providerId: str
    mediaType: str
    title: str
    originalTitle: str
    releaseDate: Optional[str] = None
    posterUrl: Optional[str] = None
    overview: str
    genres: List[str] = []

class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int
    page: int = 1
    totalPages: int = 1
    limit: int = 10
