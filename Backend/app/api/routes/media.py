from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.db.session import get_db
from app.db.models import MediaAssetModel
from app.schemas.media import MediaAssetResponse

router = APIRouter()

@router.get("/media", response_model=List[MediaAssetResponse])
async def list_media_assets(
    generation_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List generated images and media assets."""
    query = select(MediaAssetModel).order_by(desc(MediaAssetModel.created_at))
    if generation_id:
        query = query.where(MediaAssetModel.generation_id == generation_id)

    query = query.limit(limit)
    assets = (await db.execute(query)).scalars().all()
    return assets

@router.delete("/media/{media_id}")
async def delete_media_asset(media_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a media asset record."""
    stmt = select(MediaAssetModel).where(MediaAssetModel.id == media_id)
    asset = (await db.execute(stmt)).scalars().first()
    if not asset:
        raise HTTPException(status_code=404, detail="Media asset not found")

    await db.delete(asset)
    await db.commit()
    return {"message": "Media asset deleted successfully", "id": media_id}
