import sys
import os
import tempfile
from pathlib import Path
import pytest
import pytest_asyncio
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Ensure Backend/ is on sys.path whether pytest is run from repo root or Backend/
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Create an isolated temporary SQLite database for tests before app/config imports
_test_db_dir = tempfile.TemporaryDirectory()
_test_db_path = Path(_test_db_dir.name) / "test_blog_studio.db"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_test_db_path.as_posix()}"

import app.db.session as session_module
from app.db.session import Base
from app.main import app

# Create a dedicated test engine and sessionmaker bound to the temp database
test_engine = create_async_engine(
    f"sqlite+aiosqlite:///{_test_db_path.as_posix()}",
    echo=False,
    connect_args={"check_same_thread": False},
)
test_async_session = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# Override engine and AsyncSessionLocal in session_module so generation_runner uses test db
session_module.engine = test_engine
session_module.AsyncSessionLocal = test_async_session

async def override_get_db():
    async with test_async_session() as session:
        try:
            yield session
        finally:
            await session.close()

app.dependency_overrides[session_module.get_db] = override_get_db

@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
def cleanup_temp_db():
    yield
    try:
        _test_db_dir.cleanup()
    except Exception:
        pass

@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    """Initialize schema in the isolated temp test database and drop tables after each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(autouse=True)
def mock_external_services(monkeypatch):
    """Ensure all external service integrations are unconfigured / mocked so tests never hit real APIs."""
    from app.services.gemini_service import gemini_service
    from app.services.tavily_service import tavily_service
    from app.services.pinecone_service import pinecone_service
    from app.services.cloudinary_service import cloudinary_service

    monkeypatch.setattr(gemini_service, "api_key", None)
    monkeypatch.setattr(tavily_service, "api_key", None)
    monkeypatch.setattr(pinecone_service, "_configured", False)
    monkeypatch.setattr(pinecone_service, "_index", None)
    monkeypatch.setattr(cloudinary_service, "_configured", False)
    pinecone_service._local_vectors.clear()

@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
