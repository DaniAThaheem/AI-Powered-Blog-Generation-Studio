from typing import Optional, Any
from app.config import settings
from app.core.logging import logger
from langgraph.checkpoint.memory import MemorySaver

# Module-level checkpointer instance and pool instance
_checkpointer_instance: Optional[Any] = None
_pool_instance: Optional[Any] = None

async def get_checkpointer() -> Any:
    global _checkpointer_instance, _pool_instance
    if _checkpointer_instance is not None:
        return _checkpointer_instance

    postgres_url = settings.POSTGRES_CHECKPOINT_URL or (
        settings.DATABASE_URL if settings.DATABASE_URL.startswith("postgresql") else None
    )

    if postgres_url:
        try:
            from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
            from psycopg_pool import AsyncConnectionPool
            from psycopg.rows import dict_row

            # Normalize asyncpg URL to standard postgresql connection string for psycopg
            clean_url = postgres_url.replace("postgresql+asyncpg://", "postgresql://")
            pool = AsyncConnectionPool(
                conninfo=clean_url,
                max_size=10,
                open=False,
                kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row}
            )
            await pool.open()
            _pool_instance = pool
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
    global _checkpointer_instance, _pool_instance
    if _pool_instance is not None:
        try:
            await _pool_instance.close()
        except Exception as e:
            logger.warning(f"Error closing checkpointer connection pool: {e}")
        _pool_instance = None
    _checkpointer_instance = None
    
    # Also reset cached compiled workflow in blog_graph if present
    try:
        import app.workflows.blog_graph as bg
        bg._compiled_workflow = None
    except Exception:
        pass
        
    logger.info("Checkpointer closed cleanly")
