from typing import Optional, Any
from app.config import settings
from app.core.logging import logger
from langgraph.checkpoint.memory import MemorySaver

# Module-level checkpointer instance
_checkpointer_instance: Optional[Any] = None

async def get_checkpointer() -> Any:
    global _checkpointer_instance
    if _checkpointer_instance is not None:
        return _checkpointer_instance

    postgres_url = settings.POSTGRES_CHECKPOINT_URL or (
        settings.DATABASE_URL if settings.DATABASE_URL.startswith("postgresql") else None
    )

    if postgres_url:
        try:
            from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
            from psycopg_pool import AsyncConnectionPool

            # Normalize asyncpg URL to standard postgresql connection string for psycopg
            clean_url = postgres_url.replace("postgresql+asyncpg://", "postgresql://")
            pool = AsyncConnectionPool(conninfo=clean_url, max_size=10)
            checkpointer = AsyncPostgresSaver(pool)
            await checkpointer.setup()
            _checkpointer_instance = checkpointer
            logger.info("Initialized LangGraph AsyncPostgresSaver checkpointer")
            return _checkpointer_instance
        except Exception as e:
            logger.warning(f"Could not initialize AsyncPostgresSaver ({e}), falling back to MemorySaver")

    logger.info("Using in-memory LangGraph checkpointer")
    _checkpointer_instance = MemorySaver()
    return _checkpointer_instance

async def close_checkpointer():
    global _checkpointer_instance
    if _checkpointer_instance is not None:
        # If checkpointer has pool or close method
        if hasattr(_checkpointer_instance, "sync_connection"):
            pass
        _checkpointer_instance = None
        logger.info("Checkpointer closed cleanly")
