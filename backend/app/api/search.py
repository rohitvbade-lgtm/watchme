from fastapi import APIRouter, HTTPException, Query
from app.schemas.search import SearchResponse
from app.services.metadata.tmdb import TMDBMetadataProvider
import logging

router = APIRouter()
logger = logging.getLogger(__name__)
provider = TMDBMetadataProvider()

@router.get("", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=1, description="Search query"),
    type: str = Query("all", description="Media type filter: movie, tv, all"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=50, description="Items per page (max 10 to be viewed at once)")
):
    # Note: Rate limiting should be added here in future versions
    if type not in ("movie", "tv", "all"):
        raise HTTPException(status_code=422, detail="Invalid media type")
        
    logger.info(f"Search request: q='{q}', type='{type}', page={page}, limit={limit}")
    
    try:
        search_res = await provider.search(query=q, media_type=type, page=page, limit=limit)
    except TypeError:
        search_res = await provider.search(query=q, media_type=type)

    if isinstance(search_res, tuple) and len(search_res) >= 2:
        results = search_res[0]
        total = search_res[1]
    else:
        results = search_res
        total = len(results)
    
    total_pages = max(1, (total + limit - 1) // limit) if total > 0 else 1

    return SearchResponse(
        results=results,
        total=total,
        page=page,
        totalPages=total_pages,
        limit=limit
    )
