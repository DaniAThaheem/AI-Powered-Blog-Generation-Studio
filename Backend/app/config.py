from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import os
from pathlib import Path

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI-Powered Technical Blog Generation Studio"
    API_V1_STR: str = "/api"
    ENV: str = "development"
    DEBUG: bool = True

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Google Gemini
    GOOGLE_API_KEY: Optional[str] = Field(default=None, description="Google AI Studio API key")
    GEMINI_TEXT_MODEL: str = Field(default="gemini-2.5-flash", description="Gemini text generation model")
    GEMINI_IMAGE_MODEL: str = Field(default="gemini-3.1-flash-image", description="Image generation model")
    GEMINI_EMBEDDING_MODEL: str = Field(default="models/gemini-embedding-2", description="Embedding model")

    # Tavily Web Search
    TAVILY_API_KEY: Optional[str] = Field(default=None, description="Tavily API key for web research")

    # Database & LangGraph Checkpointer
    # If DATABASE_URL is postgresql, asyncpg driver will be used for application DB
    # If not provided, defaults to local SQLite with aiosqlite for instant local operation
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./blog_studio.db", description="Database connection string")
    POSTGRES_CHECKPOINT_URL: Optional[str] = Field(default=None, description="Direct postgres connection string for PostgresSaver")

    # Pinecone Vector DB
    PINECONE_API_KEY: Optional[str] = Field(default=None, description="Pinecone API key for RAG")
    PINECONE_INDEX_NAME: str = Field(default="blog-rag", description="Pinecone index name")
    PINECONE_NAMESPACE_PREFIX: str = Field(default="blog_docs", description="Namespace prefix")
    PINECONE_ENVIRONMENT: Optional[str] = Field(default=None, description="Pinecone region/env")

    # Cloudinary Storage
    CLOUDINARY_CLOUD_NAME: Optional[str] = Field(default=None, description="Cloudinary cloud name")
    CLOUDINARY_API_KEY: Optional[str] = Field(default=None, description="Cloudinary API key")
    CLOUDINARY_API_SECRET: Optional[str] = Field(default=None, description="Cloudinary API secret")
    CLOUDINARY_FOLDER: str = Field(default="blog_studio", description="Cloudinary asset folder")

    # Local Storage fallback for documents & images
    STORAGE_DIR: str = Field(default="./storage", description="Local storage fallback directory")
    MAX_UPLOAD_SIZE_MB: int = 25

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Ensure local storage directory exists
os.makedirs(settings.STORAGE_DIR, exist_ok=True)
os.makedirs(os.path.join(settings.STORAGE_DIR, "documents"), exist_ok=True)
os.makedirs(os.path.join(settings.STORAGE_DIR, "images"), exist_ok=True)
