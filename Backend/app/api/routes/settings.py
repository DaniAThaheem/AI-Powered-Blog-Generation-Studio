from fastapi import APIRouter
from app.config import settings
from app.services.gemini_service import gemini_service
from app.services.tavily_service import tavily_service
from app.services.pinecone_service import pinecone_service
from app.services.cloudinary_service import cloudinary_service

router = APIRouter()

@router.get("/settings")
async def get_settings():
    """Retrieve non-sensitive application settings and provider configuration status."""
    return {
        "app_name": settings.PROJECT_NAME,
        "environment": settings.ENV,
        "max_upload_size_mb": settings.MAX_UPLOAD_SIZE_MB,
        "models": {
            "text_model": settings.GEMINI_TEXT_MODEL,
            "image_model": settings.GEMINI_IMAGE_MODEL,
            "embedding_model": settings.GEMINI_EMBEDDING_MODEL
        },
        "providers": {
            "gemini": {
                "name": "Google Gemini",
                "configured": gemini_service.is_configured
            },
            "tavily": {
                "name": "Tavily Search",
                "configured": tavily_service.is_configured
            },
            "pinecone": {
                "name": "Pinecone Vector DB",
                "configured": pinecone_service.is_configured,
                "index_name": settings.PINECONE_INDEX_NAME
            },
            "cloudinary": {
                "name": "Cloudinary Media",
                "configured": cloudinary_service.is_configured
            },
            "database": {
                "name": "PostgreSQL / SQLite",
                "type": "postgresql" if settings.DATABASE_URL.startswith("postgresql") else "sqlite"
            }
        }
    }
