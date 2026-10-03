from pydantic import BaseModel, ConfigDict, Field, AliasChoices
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from uuid import UUID

class MediaItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    
    id: UUID
    provider: str
    providerId: str = Field(validation_alias=AliasChoices("provider_id", "providerId"))
    mediaType: str = Field(validation_alias=AliasChoices("media_type", "mediaType"))
    title: str
    originalTitle: Optional[str] = Field(default=None, validation_alias=AliasChoices("original_title", "originalTitle"))
    overview: Optional[str] = None
    posterPath: Optional[str] = Field(default=None, validation_alias=AliasChoices("poster_path", "posterPath"))
    backdropPath: Optional[str] = Field(default=None, validation_alias=AliasChoices("backdrop_path", "backdropPath"))
    releaseDate: Optional[date] = Field(default=None, validation_alias=AliasChoices("release_date", "releaseDate"))
    firstAirDate: Optional[date] = Field(default=None, validation_alias=AliasChoices("first_air_date", "firstAirDate"))
    runtime: Optional[int] = None
    genres: List[Dict[str, Any]] = Field(default_factory=list, validation_alias=AliasChoices("genres_json", "genres"))
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, validation_alias=AliasChoices("metadata_json", "metadata"))
    rating: Optional[float] = None
    voteCount: Optional[int] = Field(default=None, validation_alias=AliasChoices("vote_count", "voteCount"))
    popularity: Optional[float] = None
    originalLanguage: Optional[str] = Field(default=None, validation_alias=AliasChoices("original_language", "originalLanguage"))
    adult: bool = False
    createdAt: Optional[datetime] = Field(default=None, validation_alias=AliasChoices("created_at", "createdAt"))
    updatedAt: Optional[datetime] = Field(default=None, validation_alias=AliasChoices("updated_at", "updatedAt"))

    # Backward-compatibility property getters for ORM-style snake_case access
    @property
    def provider_id(self) -> str:
        return self.providerId

    @property
    def media_type(self) -> str:
        return self.mediaType

    @property
    def original_title(self) -> Optional[str]:
        return self.originalTitle

    @property
    def poster_path(self) -> Optional[str]:
        return self.posterPath

    @property
    def backdrop_path(self) -> Optional[str]:
        return self.backdropPath

    @property
    def release_date(self) -> Optional[date]:
        return self.releaseDate

    @property
    def first_air_date(self) -> Optional[date]:
        return self.firstAirDate

    @property
    def genres_json(self) -> List[Dict[str, Any]]:
        return self.genres

    @property
    def metadata_json(self) -> Optional[Dict[str, Any]]:
        return self.metadata

    @property
    def vote_count(self) -> Optional[int]:
        return self.voteCount

    @property
    def original_language(self) -> Optional[str]:
        return self.originalLanguage

    @property
    def created_at(self) -> Optional[datetime]:
        return self.createdAt

    @property
    def updated_at(self) -> Optional[datetime]:
        return self.updatedAt
