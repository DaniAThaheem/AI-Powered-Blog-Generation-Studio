"""Tests for document upload filename sanitization."""
import io
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_hostile_filename_is_sanitized(async_client: AsyncClient, monkeypatch, tmp_path):
    """Directory traversal filenames like ../../etc/passwd.txt must be sanitized to basename only."""
    from app.services.document_service import document_service
    from app.config import settings

    # Point STORAGE_DIR to temp dir so we can inspect the result
    monkeypatch.setattr(settings, "STORAGE_DIR", str(tmp_path))

    # Mock process_and_index_document to capture arguments and return a fake model
    from app.db.models import DocumentModel
    from datetime import datetime, timezone

    fake_doc = DocumentModel(
        id="doc-123",
        filename="stored_passwd.txt",
        original_name="passwd.txt",
        file_type="txt",
        file_size=13,
        storage_path="/tmp/stored_passwd.txt",
        cloudinary_url=None,
        status="ready",
        embedding_model="fallback_hash",
        chunk_count=1,
        extracted_text_preview="Hello, world!",
        error_message=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    captured = {}

    async def mock_process(db, file_path, original_filename, file_type, file_size):
        captured["file_path"] = file_path
        captured["original_filename"] = original_filename
        return fake_doc

    monkeypatch.setattr(document_service, "process_and_index_document", mock_process)

    # Upload with a hostile filename containing directory traversal
    content = b"Hello, world!"
    res = await async_client.post(
        "/api/documents/upload",
        files={"file": ("../../etc/passwd.txt", io.BytesIO(content), "text/plain")},
    )
    assert res.status_code == 201
    # The original_filename passed to the service should be just "passwd.txt"
    assert captured["original_filename"] == "passwd.txt"
    # The stored file path should NOT contain ".." components
    assert ".." not in captured["file_path"]


@pytest.mark.asyncio
async def test_dotdot_only_filename_gets_fallback(async_client: AsyncClient, monkeypatch, tmp_path):
    """A filename that resolves to '..' or '.' after sanitization gets the fallback name."""
    from app.services.document_service import document_service
    from app.config import settings

    monkeypatch.setattr(settings, "STORAGE_DIR", str(tmp_path))

    # The upload should be rejected because ".." has no valid extension
    content = b"data"
    res = await async_client.post(
        "/api/documents/upload",
        files={"file": ("..", io.BytesIO(content), "text/plain")},
    )
    # ".." → fallback "uploaded_file" → no extension → 400 unsupported extension
    assert res.status_code == 400
    assert "Unsupported file extension" in res.json()["detail"]


@pytest.mark.asyncio
async def test_backslash_traversal_sanitized(async_client: AsyncClient, monkeypatch, tmp_path):
    """Windows-style backslash traversal paths are also sanitized."""
    from app.services.document_service import document_service
    from app.config import settings

    monkeypatch.setattr(settings, "STORAGE_DIR", str(tmp_path))

    from app.db.models import DocumentModel
    from datetime import datetime, timezone

    fake_doc = DocumentModel(
        id="doc-456",
        filename="stored_secret.md",
        original_name="secret.md",
        file_type="md",
        file_size=5,
        storage_path="/tmp/stored_secret.md",
        cloudinary_url=None,
        status="ready",
        embedding_model="fallback_hash",
        chunk_count=1,
        extracted_text_preview="# Doc",
        error_message=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    captured = {}

    async def mock_process(db, file_path, original_filename, file_type, file_size):
        captured["original_filename"] = original_filename
        return fake_doc

    monkeypatch.setattr(document_service, "process_and_index_document", mock_process)

    content = b"# Doc"
    res = await async_client.post(
        "/api/documents/upload",
        files={"file": ("..\\..\\secret.md", io.BytesIO(content), "text/plain")},
    )
    assert res.status_code == 201
    # On Windows Path("..\\..\\secret.md").name → "secret.md"
    assert captured["original_filename"] == "secret.md"
