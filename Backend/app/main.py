from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import asyncio

from app.config import settings
from app.core.logging import setup_logging, logger
from app.db.session import init_db
from app.db.checkpointer import close_checkpointer
from app.api.routes.health import router as health_router
from app.api.routes.generations import router as generations_router
from app.api.routes.documents import router as documents_router
from app.api.routes.media import router as media_router
from app.api.routes.chat import router as chat_router
from app.api.routes.settings import router as settings_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    logger.info(f"Starting {settings.PROJECT_NAME} backend...")
    await init_db()
    from app.services.generation_runner import generation_runner
    await generation_runner.cleanup_orphaned_generations()
    from app.services.document_service import document_service
    asyncio.create_task(document_service.reindex_all_documents())
    from app.services.pinecone_service import pinecone_service
    if pinecone_service.warning:
        logger.warning(f"Pinecone startup warning: {pinecone_service.warning}")
    yield
    # Shutdown
    logger.info("Shutting down backend...")
    await close_checkpointer()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Full-stack AI-Powered Technical Blog Generation Studio with LangGraph, Gemini, Tavily, Pinecone, and Cloudinary",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow configured origins and dev proxy
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount local storage directory for static assets (images, documents)
os.makedirs(settings.STORAGE_DIR, exist_ok=True)
os.makedirs(os.path.join(settings.STORAGE_DIR, "images"), exist_ok=True)
os.makedirs(os.path.join(settings.STORAGE_DIR, "documents"), exist_ok=True)
app.mount("/api/storage", StaticFiles(directory=settings.STORAGE_DIR), name="storage")

# Include API Routers
app.include_router(health_router, prefix="/api", tags=["Health"])
app.include_router(generations_router, prefix="/api", tags=["Generations"])
app.include_router(documents_router, prefix="/api", tags=["Documents"])
app.include_router(media_router, prefix="/api", tags=["Media"])
app.include_router(chat_router, prefix="/api", tags=["Chat"])
app.include_router(settings_router, prefix="/api", tags=["Settings"])

@app.get("/")
async def root():
    return {
        "message": "AI-Powered Technical Blog Generation Studio API is running",
        "docs_url": "/docs",
        "health_url": "/api/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
