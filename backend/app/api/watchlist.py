from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone
import uuid

from app.db.session import get_db
from app.schemas.watchlist import WatchlistAddRequest, WatchlistItemSchema, WatchlistResponse
from app.models.watchlist_item import WatchlistItem
from app.models.media_item import MediaItem
from app.services.metadata.tmdb import TMDBMetadataProvider

router = APIRouter()
provider = TMDBMetadataProvider()

@router.get("", response_model=WatchlistResponse)
async def get_watchlist(
    device_id: str = Query(...),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=50, description="Items per page (max 10 to be viewed at once)"),
    all_items: bool = Query(False, description="Fetch all items (useful for sync)"),
    db: AsyncSession = Depends(get_db)
):
    count_stmt = select(func.count(WatchlistItem.id)).where(WatchlistItem.device_id == device_id)
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = (
        select(WatchlistItem)
        .where(WatchlistItem.device_id == device_id)
        .options(selectinload(WatchlistItem.media_item))
        .order_by(WatchlistItem.added_at.desc())
    )
    if not all_items:
        stmt = stmt.offset((page - 1) * limit).limit(limit)

    result = await db.execute(stmt)
    items = result.scalars().all()

    total_pages = max(1, (total + limit - 1) // limit) if total > 0 else 1

    return WatchlistResponse(
        items=[WatchlistItemSchema.from_orm_item(item) for item in items],
        total=total,
        page=page if not all_items else 1,
        totalPages=total_pages if not all_items else 1,
        limit=limit if not all_items else (total or limit)
    )

@router.post("", response_model=WatchlistItemSchema)
async def add_to_watchlist(
    request: WatchlistAddRequest, 
    device_id: str = Query(...), 
    db: AsyncSession = Depends(get_db)
):
    # Check if media item already in cache
    stmt = select(MediaItem).where(
        MediaItem.provider == request.provider,
        MediaItem.provider_id == request.providerId,
        MediaItem.media_type == request.mediaType
    )
    result = await db.execute(stmt)
    media_item = result.scalar_one_or_none()
    
    if not media_item:
        # Fetch from TMDB
        schema = await provider.get_details(request.providerId, request.mediaType)
        if not schema:
            raise HTTPException(status_code=404, detail="Media item not found")
            
        media_item = MediaItem(
            id=schema.id,
            provider="tmdb",
            provider_id=request.providerId,
            media_type=request.mediaType,
            title=schema.title,
            original_title=schema.original_title,
            overview=schema.overview,
            poster_path=schema.poster_path,
            backdrop_path=schema.backdrop_path,
            release_date=schema.release_date,
            first_air_date=schema.first_air_date,
            runtime=schema.runtime,
            genres_json=schema.genres_json,
            metadata_json=schema.metadata_json,
            rating=schema.rating,
            vote_count=schema.vote_count,
            popularity=schema.popularity,
            original_language=schema.original_language,
            adult=schema.adult
        )
        db.add(media_item)
        try:
            await db.flush()
        except IntegrityError:
            await db.rollback()
            result = await db.execute(stmt)
            media_item = result.scalar_one()
            
    watchlist_item = WatchlistItem(
        device_id=device_id,
        media_item_id=media_item.id
    )
    db.add(watchlist_item)
    try:
        await db.commit()
        await db.refresh(watchlist_item)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Item already in watchlist")
        
    watchlist_item.media_item = media_item
    return WatchlistItemSchema.from_orm_item(watchlist_item)

@router.delete("/{id}")
async def delete_from_watchlist(
    id: uuid.UUID,
    device_id: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(WatchlistItem).where(WatchlistItem.id == id, WatchlistItem.device_id == device_id)
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
        
    await db.delete(item)
    await db.commit()
    return {"status": "ok"}

@router.post("/{id}/watched")
async def mark_watched(
    id: uuid.UUID,
    device_id: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(WatchlistItem).where(WatchlistItem.id == id, WatchlistItem.device_id == device_id).options(selectinload(WatchlistItem.media_item))
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
        
    item.watched = True
    item.watched_at = datetime.now(timezone.utc)
    await db.commit()
    return WatchlistItemSchema.from_orm_item(item)

@router.post("/{id}/unwatched")
async def mark_unwatched(
    id: uuid.UUID,
    device_id: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(WatchlistItem).where(WatchlistItem.id == id, WatchlistItem.device_id == device_id).options(selectinload(WatchlistItem.media_item))
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
        
    item.watched = False
    item.watched_at = None
    await db.commit()
    return WatchlistItemSchema.from_orm_item(item)
