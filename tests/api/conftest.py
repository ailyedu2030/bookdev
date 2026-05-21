"""
Test Configuration and Fixtures for API Integration Tests

This module provides pytest fixtures for testing the FastAPI application.
"""

import os
import sys
from collections.abc import Generator
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
sys.path.insert(0, src_path)

from api.deps import (
    DatabaseSession,
    User,
    create_access_token,
    create_refresh_token,
    generate_uuid,
    get_db,
    get_password_hash,
)
from api.middleware.csrf import csrf_protect, csrf_token_manager
from api.router import api_router
from api.routes.workflows import _workflows_store


class TestDatabaseSession(DatabaseSession):
    """In-memory test database session"""

    def __init__(self):
        super().__init__()
        self._reset()

    def _reset(self):
        """Reset all data"""
        self._users.clear()
        self._projects.clear()
        self._chapters.clear()
        self._terms.clear()
        self._concepts.clear()
        self._sections.clear()
        self._sessions.clear()
        self._user_passwords: dict = {}

    def create_user(self, user_data: dict) -> User:
        if "password" in user_data:
            self._user_passwords[user_data["email"]] = user_data["password"]
            user_data["password_hash"] = get_password_hash(user_data.pop("password"))
        return super().create_user(user_data)

    def get_user_by_email(self, email: str) -> User | None:
        for user in self._users.values():
            if user.email == email:
                return user
        return None

    def verify_user_password(self, email: str, password: str) -> bool:
        stored_hash = self._user_passwords.get(email)
        if not stored_hash:
            return False
        return stored_hash == password


@pytest.fixture
def test_db() -> TestDatabaseSession:
    """Create a fresh in-memory database for each test"""
    db = TestDatabaseSession()
    yield db
    db._reset()


@pytest.fixture(autouse=True)
def clear_workflows_store():
    """Clear workflows store before each test to prevent cross-test pollution"""
    _workflows_store.clear()
    yield


@pytest.fixture(autouse=True)
def clear_knowledge_graph():
    """Clear knowledge graph in-memory stores before each test"""
    from api.routes import knowledge_graph as kg_module
    kg_module._in_memory_nodes.clear()
    kg_module._in_memory_edges.clear()
    kg_module._edge_id_counter = 0
    yield


@pytest.fixture
def test_app(test_db: TestDatabaseSession) -> FastAPI:
    """Create FastAPI application with test dependencies"""
    app = FastAPI(title="Test API")
    app.include_router(api_router)

    async def override_get_db():
        return test_db

    async def override_csrf_protect():
        return None

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[csrf_protect] = override_csrf_protect

    with patch("api.middleware.rate_limit.rate_limiter.check_rate_limit", new_callable=AsyncMock) as mock_rate_limit:
        async def allow_all(*args, **kwargs):
            return (True, 100, 0)
        mock_rate_limit.side_effect = allow_all

        with patch("api.routes.auth.verify_password") as mock_verify:
            def verify_always_true(*args, **kwargs):
                return True
            mock_verify.side_effect = verify_always_true

            yield app

    test_db._reset()
    _workflows_store.clear()


@pytest.fixture
def test_client(test_app: FastAPI) -> Generator[TestClient, None, None]:
    """Create synchronous test client"""
    with TestClient(test_app) as client:
        yield client


@pytest.fixture
def test_user(test_db: TestDatabaseSession) -> User:
    """Create a test user with viewer role"""
    user = test_db.create_user({
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "testpassword123",
        "role": "viewer",
        "organization_id": "test-org-123",
        "clearance_level": 1,
    })
    return user


@pytest.fixture
def test_user_authenticated(test_db: TestDatabaseSession, test_user: User) -> dict:
    """Create authenticated test user with tokens"""
    user = test_user
    access_token = create_access_token({
        "sub": user.id,
        "email": user.email,
        "role": user.role,
    })
    refresh_token = create_refresh_token({
        "sub": user.id,
        "email": user.email,
        "role": user.role,
    })
    test_db.add_session(user.id, access_token)

    return {
        "user": user,
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


@pytest.fixture
def test_admin(test_db: TestDatabaseSession) -> User:
    """Create a test admin user"""
    admin = test_db.create_user({
        "username": "testadmin",
        "email": "testadmin@example.com",
        "password": "adminpassword123",
        "role": "system_admin",
        "organization_id": "test-org-123",
        "clearance_level": 5,
    })
    return admin


@pytest.fixture
def test_admin_authenticated(test_db: TestDatabaseSession, test_admin: User) -> dict:
    """Create authenticated admin user with tokens"""
    user = test_admin
    access_token = create_access_token({
        "sub": user.id,
        "email": user.email,
        "role": user.role,
    })
    refresh_token = create_refresh_token({
        "sub": user.id,
        "email": user.email,
        "role": user.role,
    })
    test_db.add_session(user.id, access_token)

    return {
        "user": test_admin,
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


@pytest.fixture
def author_user(test_db: TestDatabaseSession) -> User:
    """Create a test author user"""
    author = test_db.create_user({
        "username": "testauthor",
        "email": "testauthor@example.com",
        "password": "authorpassword123",
        "role": "author",
        "organization_id": "test-org-123",
        "clearance_level": 2,
    })
    return author


@pytest.fixture
def author_authenticated(test_db: TestDatabaseSession, author_user: User) -> dict:
    """Create authenticated author user with tokens"""
    access_token = create_access_token({
        "sub": author_user.id,
        "email": author_user.email,
        "role": author_user.role,
        "organization_id": author_user.organization_id,
        "clearance_level": author_user.clearance_level,
    })
    refresh_token = create_refresh_token({
        "sub": author_user.id,
        "email": author_user.email,
        "role": author_user.role,
        "organization_id": author_user.organization_id,
        "clearance_level": author_user.clearance_level,
    })
    test_db.add_session(author_user.id, access_token)

    return {
        "user": author_user,
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


@pytest.fixture
def reviewer_user(test_db: TestDatabaseSession) -> User:
    """Create a test reviewer user"""
    reviewer = test_db.create_user({
        "username": "testreviewer",
        "email": "testreviewer@example.com",
        "password": "reviewerpassword123",
        "role": "reviewer",
        "organization_id": "test-org-123",
        "clearance_level": 3,
    })
    return reviewer


@pytest.fixture
def reviewer_authenticated(test_db: TestDatabaseSession, reviewer_user: User) -> dict:
    """Create authenticated reviewer user with tokens"""
    access_token = create_access_token({
        "sub": reviewer_user.id,
        "email": reviewer_user.email,
        "role": reviewer_user.role,
        "organization_id": reviewer_user.organization_id,
        "clearance_level": reviewer_user.clearance_level,
    })
    refresh_token = create_refresh_token({
        "sub": reviewer_user.id,
        "email": reviewer_user.email,
        "role": reviewer_user.role,
        "organization_id": reviewer_user.organization_id,
        "clearance_level": reviewer_user.clearance_level,
    })
    test_db.add_session(reviewer_user.id, access_token)

    return {
        "user": reviewer_user,
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


@pytest.fixture
def editor_user(test_db: TestDatabaseSession) -> User:
    """Create a test editor user"""
    editor = test_db.create_user({
        "username": "testeditor",
        "email": "testeditor@example.com",
        "password": "editorpassword123",
        "role": "editor",
        "organization_id": "test-org-123",
        "clearance_level": 4,
    })
    return editor


@pytest.fixture
def editor_authenticated(test_db: TestDatabaseSession, editor_user: User) -> dict:
    """Create authenticated editor user with tokens"""
    access_token = create_access_token({
        "sub": editor_user.id,
        "email": editor_user.email,
        "role": editor_user.role,
        "organization_id": editor_user.organization_id,
        "clearance_level": editor_user.clearance_level,
    })
    refresh_token = create_refresh_token({
        "sub": editor_user.id,
        "email": editor_user.email,
        "role": editor_user.role,
        "organization_id": editor_user.organization_id,
        "clearance_level": editor_user.clearance_level,
    })
    test_db.add_session(editor_user.id, access_token)

    return {
        "user": editor_user,
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


@pytest.fixture
def content_admin_user(test_db: TestDatabaseSession) -> User:
    """Create a test content admin user"""
    admin = test_db.create_user({
        "username": "testcontentadmin",
        "email": "testcontentadmin@example.com",
        "password": "contentadminpassword123",
        "role": "content_admin",
        "organization_id": "test-org-123",
        "clearance_level": 5,
    })
    return admin


@pytest.fixture
def content_admin_authenticated(test_db: TestDatabaseSession, content_admin_user: User) -> dict:
    """Create authenticated content admin user with tokens"""
    access_token = create_access_token({
        "sub": content_admin_user.id,
        "email": content_admin_user.email,
        "role": content_admin_user.role,
    })
    refresh_token = create_refresh_token({
        "sub": content_admin_user.id,
        "email": content_admin_user.email,
        "role": content_admin_user.role,
    })
    test_db.add_session(content_admin_user.id, access_token)

    return {
        "user": content_admin_user,
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


def get_auth_header(token: str) -> dict:
    """Create authorization header"""
    return {"Authorization": f"Bearer {token}"}


def get_csrf_headers(token: str = None) -> dict:
    """Create headers with CSRF token"""
    csrf_token = csrf_token_manager.generate_token()
    headers = {"X-CSRF-Token": csrf_token}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def create_test_project(test_db: TestDatabaseSession, owner_id: str, **kwargs) -> dict:
    """Helper to create a test project"""
    project_id = generate_uuid()
    project = {
        "id": project_id,
        "name": kwargs.get("name", f"Test Project {project_id[:8]}"),
        "description": kwargs.get("description", "Test project description"),
        "status": kwargs.get("status", "draft"),
        "owner_id": owner_id,
        "total_chapters": kwargs.get("total_chapters", 0),
        "current_progress": kwargs.get("current_progress", 0),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    test_db._projects[project_id] = project
    return project


def create_test_user(test_db: TestDatabaseSession, **kwargs) -> User:
    """Helper to create a test user"""
    email = kwargs.get("email", f"testuser-{generate_uuid()[:8]}@example.com")
    password = kwargs.get("password", "testpassword123")
    user = test_db.create_user({
        "username": kwargs.get("username", f"testuser-{generate_uuid()[:8]}"),
        "email": email,
        "role": kwargs.get("role", "viewer"),
        "organization_id": kwargs.get("organization_id", "test-org-123"),
        "clearance_level": kwargs.get("clearance_level", 1),
    })
    test_db._user_passwords[email] = password
    return user


def create_test_chapter(
    test_db: TestDatabaseSession, project_id: str, author_id: str = None, **kwargs
) -> dict:
    """Helper to create a test chapter"""
    chapter_id = generate_uuid()
    chapter = {
        "id": chapter_id,
        "project_id": project_id,
        "title": kwargs.get("title", f"Test Chapter {chapter_id[:8]}"),
        "order_num": kwargs.get("order_num", 1),
        "status": kwargs.get("status", "draft"),
        "word_count": kwargs.get("word_count", 0),
        "version": kwargs.get("version", "1.0"),
        "content_hash": kwargs.get("content_hash", ""),
        "parent_chapter_id": kwargs.get("parent_chapter_id"),
        "author_id": author_id,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    test_db._chapters[chapter_id] = chapter
    return chapter


def create_test_section(test_db: TestDatabaseSession, chapter_id: str, **kwargs) -> dict:
    """Helper to create a test section"""
    section_id = kwargs.get("id", generate_uuid())
    section = {
        "id": section_id,
        "chapter_id": chapter_id,
        "title": kwargs.get("title", f"Test Section {section_id[:8]}"),
        "order_num": kwargs.get("order_num", 1),
        "status": kwargs.get("status", "draft"),
        "word_count": kwargs.get("word_count", 0),
        "parent_section_id": kwargs.get("parent_section_id"),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    test_db._sections[section_id] = section
    return section


def create_test_term(test_db: TestDatabaseSession, **kwargs) -> dict:
    """Helper to create a test term"""
    term_id = generate_uuid()
    term = {
        "id": term_id,
        "term": kwargs.get("term", f"Test Term {term_id[:8]}"),
        "definition": kwargs.get("definition", "Test definition"),
        "domain": kwargs.get("domain"),
        "synonyms": kwargs.get("synonyms", []),
        "locked": kwargs.get("locked", False),
        "lock_reason": kwargs.get("lock_reason"),
        "version": kwargs.get("version", 1),
        "first_defined_at": kwargs.get("first_defined_at"),
        "usage_locations": kwargs.get("usage_locations", []),
        "created_at": datetime.utcnow().isoformat(),
    }
    test_db._terms[term_id] = term
    return term


@pytest.fixture
def mock_kafka_producer():
    """Mock Kafka producer for testing"""
    with patch("aiokafka.AIOKafkaProducer") as mock:
        producer = AsyncMock()
        producer.start = AsyncMock()
        producer.stop = AsyncMock()
        producer.send_and_wait = AsyncMock(return_value=MagicMock(
            partition=MagicMock(return_value=0),
            offset=MagicMock(return_value=1),
        ))
        mock.return_value = producer
        yield producer


@pytest.fixture
def mock_temporal_client():
    """Mock Temporal client for testing"""
    with patch("temporalio.client.Client") as mock:
        client = AsyncMock()
        mock.return_value = client
        yield client


@pytest.fixture
def mock_minimax_client():
    """Mock MiniMax client for testing"""
    with patch("aiohttp.ClientSession") as mock:
        session = AsyncMock()
        mock.return_value = session
        session.post = AsyncMock(return_value=AsyncMock(
            json=AsyncMock(return_value={
                "choices": [{"message": {"content": "Generated content"}}]
            })
        ))
        yield session


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing"""
    with patch("fakeredis.FakeRedis") as mock:
        redis_client = MagicMock()
        mock.return_value = redis_client
        yield redis_client
