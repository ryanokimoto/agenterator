import pytest
import asyncio
import sys
from pathlib import Path
from typing import Generator, AsyncGenerator
from unittest.mock import Mock
import tempfile
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from httpx import AsyncClient
import redis

from app.main import app
from app.core.config import settings
from app.models.user import Base
from app.api.deps import get_db
from tests import TEST_CONFIG
from tests.utils.factories import UserFactory, DocumentFactory
from tests.utils.database import TestDatabase
from tests.utils.auth import AuthHelper

# ==================== Database Fixtures ====================

@pytest.fixture(scope="session")
def event_loop():
    """Loop for AsyncIO tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_db_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()

@pytest.fixture(scope="function")
def db_session(test_db_engine) -> Generator[Session, None, None]:
    """Create a new database session for each test."""
    connection = test_db_engine.connect()
    transaction = connection.begin()
    
    TestSessionLocal = sessionmaker(
        auto_commit=False,
        autoflush=False,
        bind=connection,
        expire_on_commit=False,
    )

    session = TestSessionLocal()
    session.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, transaction):
        if transaction.nested and not transaction._parent.nested:
            session.expire_all()
            session.begin_nested()
    yield session

    session.close()
    transaction.rollback()
    connection.close()

# ==================== Application Fixtures ====================

@pytest.fixture(scope="session")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependecy_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client
    
    app.dependecy_overrides.clear()

@pytest.fixture(scope="session")
async def async_client(db_session: Session) -> AsyncGenerator[AsyncClient, None]:
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependecy_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as async_test_client:
        yield async_test_client
    
    app.dependecy_overrides.clear()

# ==================== Authentication Fixtures ====================

@pytest.fixture
def auth_helper(client: TestClient, db_session: Session) -> AuthHelper:
    return AuthHelper(client, db_session)

@pytest.fixture
def test_user(db_session: Session):
    user = UserFactory.create()
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def admin_user(db_session: Session):
    user = UserFactory.create(is_superuser=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def authenticated_client(client: TestClient, test_user) -> TestClient:
    from app.core.security import create_access_token
    token = create_access_token(data={"sub": test_user.id})
    client.headers = {"Authorization": f"Bearer {token}"}
    return client

@pytest.fixture
def auth_headers(test_user) -> dict:
    from app.core.security import create_access_token
    token = create_access_token(data={"sub": test_user.id})
    return {"Authorization": f"Bearer {token}"}

# ==================== Document Fixtures ====================

@pytest.fixture
def test_document(db_session: Session, test_user):
    document = DocumentFactory.create(user_id=test_user.id)
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    return document

@pytest.fixture
def test_documents(db_session: Session, test_user):
    documents = DocumentFactory.create_batch(5, user_id=test_user.id)
    for doc in docs:
        db_session.add(doc)
    db_session.commit()
    return documents

# ==================== File Handling Fixtures ====================

@pytest.fixture
def temp_upload_dir():
    temp_dir = tempfile.mkdtemp()
    for subdir in ["pdf", "docx", "txt", "pptx"]:
        Path(temp_dir, subdir).mkdir(exist_ok=True)
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_pdf_file():
    from io import BytesIO
    pdf_content = b"%PDF-1.4\n%Test PDF file content\n"
    return BytesIO(pdf_content)

@pytest.fixture
def sample_text_file():
    from io import BytesIO
    content = b"This is a test document for the RAG platform.\n" * 10
    return BytesIO(content)

@pytest.fixture
def mock_file_upload(temp_upload_dir):
    from app.services.file_service import file_service
    original_dir = file_service.UPLOAD_DIR
    file_service.UPLOAD_DIR = Path(temp_upload_dir)
    yield file_service
    file_service.UPLOAD_DIR = original_dir

@pytest.fixture
def mock_redis():
    mock = Mock()
    mock.get_return_value = None
    mock.set.return_value = True
    mock.delete.return_value = True
    mock.exists.return_value = False
    return mock

@pytest.fixture
def mock_openai():
    mock = Mock()
    mock.embeddings.create.return_value = Mock(
        data=[Mock(embedding=[0.1] * 1536)],
    )
    mock.chat.completions.create.return_value = Mock(
        choices=[Mock(message=Mock(content="Test response"))],
    )
    return mock

@pytest.fixture
def mock_celery_task():
    mock = Mock()
    mock.delay.return_value = Mock(id="mock_task_id")
    mock.apply_async.return_value = Mock(id="mock_task_id")
    return mock

# ==================== Test Data Fixtures ====================

@pytest.fixture
def sample_user_data():
    return {
        "email": "testuser@example.com",
        "user": "testuser",
        "password": "TestPassword123!",
    }

@pytest.fixture
def sample_document_data():
    return {
        "filename": "test_document.pdf",
        "file_type": "pdf",
        "file_size": 1024,
        "content": "This is the content of the test document.",
    }

# ==================== Performance Testing Fixtures ====================

@pytest.fixture
def benchmark_client(client: TestClient):
    import logging
    logging.disable(logging.CRITICAL)
    yield client
    logging.disable(logging.NOTSET)

# ==================== Cleanup Fixtures ====================

@pytest.fixture(auto_use=True)
def cleanup_uploads(temp_upload_dir):
    yield
    for file_path in Path(temp_upload_dir).rglob("*"):
        if file_path.is_file():
            file_path.unlink()

@pytest.fixture(auto_use=True)
def reset_singletons():
    # add singleton reset logic here if needed
    yield

# ==================== Configuration Fixtures ====================

@pytest.fixture
def test_settings():
    original_settings = {}
    for key in ["DATABASE_URL", "REDIS_URL", "SECRET_KEY"]:
        original_settings[key] = getattr(settings, key, None)

    settings.DATABASE_URL = TEST_CONFIG["test_database_url"]
    settings.REDIS_URL = TEST_CONFIG["test_redis_url"]
    settings.SECRET_KEY = "test-secret-key"

    yield settings

    for key, value in original_settings.items():
        setattr(settings, key, value)