from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.session import get_db
from app.config import settings
from app.services.gemini_service import gemini_service
from app.services.tavily_service import tavily_service
from app.services.pinecone_service import pinecone_service
from app.services.cloudinary_service import cloudinary_service

router = APIRouter()

@router.get("/health")
async def get_health(db: AsyncSession = Depends(get_db)):
    """Health check endpoint checking all integrated services."""
    db_ok = False
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    return {
        "status": "healthy" if db_ok else "degraded",
        "database": {
            "status": "connected" if db_ok else "disconnected",
            "type": "postgresql" if settings.DATABASE_URL.startswith("postgresql") else "sqlite"
        },
        "services": {
            "gemini": {
                "configured": gemini_service.is_configured,
                "text_model": settings.GEMINI_TEXT_MODEL,
                "image_model": settings.GEMINI_IMAGE_MODEL
            },
            "tavily": {
                "configured": tavily_service.is_configured
            },
            "pinecone": {
                "configured": pinecone_service.is_configured,
                "index_name": settings.PINECONE_INDEX_NAME
            },
            "cloudinary": {
                "configured": cloudinary_service.is_configured,
                "cloud_name": settings.CLOUDINARY_CLOUD_NAME if settings.CLOUDINARY_CLOUD_NAME else None
            }
        }
    }
