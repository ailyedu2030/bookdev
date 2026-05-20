"""Comprehensive tests for api/deps.py authentication and dependency injection functions.

Tests JWT token operations, password hashing, RBAC, and user dependencies.
"""

import uuid
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, AsyncMock, patch

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


class TestPasswordHashing:
    """Test password hashing functions."""

    def test_verify_password_correct(self):
        """Test verify_password returns True for correct password."""
        from api.deps import verify_password, get_password_hash

        hashed = get_password_hash("testpassword123")
        result = verify_password("testpassword123", hashed)
        assert result is True

    def test_verify_password_incorrect(self):
        """Test verify_password returns False for incorrect password."""
        from api.deps import verify_password, get_password_hash

        hashed = get_password_hash("correctpassword")
        result = verify_password("wrongpassword", hashed)
        assert result is False

    def test_get_password_hash_returns_string(self):
        """Test get_password_hash returns a bcrypt hash string."""
        from api.deps import get_password_hash

        result = get_password_hash("mypassword")
        assert isinstance(result, str)
        assert len(result) > 20
        assert result.startswith("$2b$")

    def test_different_hashes_for_same_password(self):
        """Test that same password produces different hashes (salt)."""
        from api.deps import get_password_hash

        hash1 = get_password_hash("samepassword")
        hash2 = get_password_hash("samepassword")
        assert hash1 != hash2


class TestJWTTokens:
    """Test JWT token creation and decoding."""

    def test_create_access_token_returns_string(self):
        """Test create_access_token returns a JWT string."""
        from api.deps import create_access_token

        token = create_access_token({"sub": "user123", "email": "test@example.com", "role": "viewer"})
        assert isinstance(token, str)
        assert len(token) > 20
        assert token.count(".") == 2

    def test_create_access_token_with_expiry(self):
        """Test create_access_token respects custom expiry."""
        from api.deps import create_access_token

        token = create_access_token(
            {"sub": "user123", "email": "test@example.com", "role": "viewer"},
            expires_delta=timedelta(hours=1)
        )
        assert isinstance(token, str)

    def test_create_refresh_token_returns_string(self):
        """Test create_refresh_token returns a JWT string."""
        from api.deps import create_refresh_token

        token = create_refresh_token({"sub": "user123"})
        assert isinstance(token, str)
        assert len(token) > 20
        assert token.count(".") == 2

    def test_decode_access_token_valid(self):
        """Test decode_token successfully decodes valid access token."""
        from api.deps import create_access_token, decode_token

        data = {"sub": "user123", "email": "test@example.com", "role": "editor"}
        token = create_access_token(data)
        token_data = decode_token(token, "access")

        assert token_data.sub == "user123"
        assert token_data.email == "test@example.com"
        assert token_data.role == "editor"
        assert token_data.type == "access"

    def test_decode_refresh_token_valid(self):
        """Test decode_token successfully decodes valid refresh token."""
        from api.deps import create_refresh_token, decode_token

        data = {"sub": "user123"}
        token = create_refresh_token(data)
        token_data = decode_token(token, "refresh")

        assert token_data.sub == "user123"
        assert token_data.type == "refresh"

    def test_decode_token_wrong_type_raises(self):
        """Test decode_token raises exception for wrong token type."""
        from api.deps import create_access_token, decode_token
        from jose import JWTError

        token = create_access_token({"sub": "user123", "email": "test@example.com", "role": "viewer"})
        with pytest.raises(HTTPException) as exc_info:
            decode_token(token, "refresh")

        assert exc_info.value.status_code == 401
        assert "TOKEN_INVALID" in str(exc_info.value.detail)

    def test_decode_token_invalid_raises(self):
        """Test decode_token raises exception for invalid token."""
        from api.deps import decode_token

        with pytest.raises(HTTPException) as exc_info:
            decode_token("invalid.token.here", "access")

        assert exc_info.value.status_code == 401

    def test_decode_token_expired(self):
        """Test decode_token raises exception for expired token."""
        from api.deps import create_access_token, decode_token, ACCESS_TOKEN_EXPIRE_MINUTES
        from datetime import timedelta

        token = create_access_token(
            {"sub": "user123", "email": "test@example.com", "role": "viewer"},
            expires_delta=timedelta(minutes=-1)
        )

        with pytest.raises(HTTPException) as exc_info:
            decode_token(token, "access")

        assert exc_info.value.status_code == 401


class TestUtilityFunctions:
    """Test utility functions."""

    def test_generate_uuid_returns_string(self):
        """Test generate_uuid returns a valid UUID string."""
        from api.deps import generate_uuid

        result = generate_uuid()
        assert isinstance(result, str)
        uuid.UUID(result)

    def test_generate_uuid_unique(self):
        """Test generate_uuid returns unique values."""
        from api.deps import generate_uuid

        uuids = [generate_uuid() for _ in range(100)]
        assert len(set(uuids)) == 100

    def test_hash_content_returns_hex(self):
        """Test hash_content returns SHA-256 hex string."""
        from api.deps import hash_content

        result = hash_content("test content")
        assert isinstance(result, str)
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_hash_content_deterministic(self):
        """Test hash_content is deterministic."""
        from api.deps import hash_content

        hash1 = hash_content("same content")
        hash2 = hash_content("same content")
        assert hash1 == hash2

    def test_hash_content_different_for_different_content(self):
        """Test hash_content produces different hashes for different content."""
        from api.deps import hash_content

        hash1 = hash_content("content a")
        hash2 = hash_content("content b")
        assert hash1 != hash2


class TestUserModel:
    """Test User dataclass."""

    def test_user_creation(self):
        """Test User creation with all fields."""
        from api.deps import User

        user = User(
            id="user123",
            username="testuser",
            email="test@example.com",
            role="editor",
            organization_id="org456",
            clearance_level=3
        )

        assert user.id == "user123"
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == "editor"
        assert user.organization_id == "org456"
        assert user.clearance_level == 3

    def test_user_defaults(self):
        """Test User creation with default values."""
        from api.deps import User

        user = User(
            id="user123",
            username="testuser",
            email="test@example.com",
            role="viewer"
        )

        assert user.organization_id is None
        assert user.clearance_level == 1


class TestTokenDataModel:
    """Test TokenData dataclass."""

    def test_token_data_creation(self):
        """Test TokenData creation."""
        from api.deps import TokenData

        now = int(datetime.now(timezone.utc).timestamp())
        token_data = TokenData(
            sub="user123",
            email="test@example.com",
            role="admin",
            exp=now + 3600,
            iat=now,
            type="access"
        )

        assert token_data.sub == "user123"
        assert token_data.email == "test@example.com"
        assert token_data.role == "admin"
        assert token_data.exp == now + 3600
        assert token_data.iat == now
        assert token_data.type == "access"


class TestRoleHierarchy:
    """Test role hierarchy and permissions."""

    def test_role_hierarchy_values(self):
        """Test role hierarchy contains expected roles."""
        from api.deps import ROLE_HIERARCHY

        assert ROLE_HIERARCHY["system_admin"] == 6
        assert ROLE_HIERARCHY["content_admin"] == 5
        assert ROLE_HIERARCHY["editor"] == 4
        assert ROLE_HIERARCHY["reviewer"] == 3
        assert ROLE_HIERARCHY["author"] == 2
        assert ROLE_HIERARCHY["viewer"] == 1

    def test_role_permissions_system_admin(self):
        """Test system_admin has all permissions."""
        from api.deps import ROLE_PERMISSIONS

        assert "*:*" in ROLE_PERMISSIONS["system_admin"]

    def test_role_permissions_content_admin(self):
        """Test content_admin has expected permissions."""
        from api.deps import ROLE_PERMISSIONS

        perms = ROLE_PERMISSIONS["content_admin"]
        assert "projects:*" in perms
        assert "chapters:*" in perms
        assert "terms:*" in perms

    def test_role_permissions_editor(self):
        """Test editor has expected permissions."""
        from api.deps import ROLE_PERMISSIONS

        perms = ROLE_PERMISSIONS["editor"]
        assert "chapters:*" in perms
        assert "projects:read" in perms

    def test_role_permissions_viewer(self):
        """Test viewer has read-only permissions."""
        from api.deps import ROLE_PERMISSIONS

        perms = ROLE_PERMISSIONS["viewer"]
        assert "projects:read" in perms
        assert "chapters:read" in perms
        assert perms == {"projects:read", "chapters:read", "terms:read", "knowledge_graph:read"}


class TestRBACChecker:
    """Test RBACChecker class."""

    def test_rbac_checker_with_valid_permission(self):
        """Test RBACChecker allows access with valid permission."""
        from api.deps import RBACChecker, User

        user = User(
            id="user123",
            username="testuser",
            email="test@example.com",
            role="editor"
        )

        checker = RBACChecker(["chapters:read"])
        result = checker(user)
        assert result == user

    def test_rbac_checker_with_wildcard_permission(self):
        """Test RBACChecker allows wildcard permission."""
        from api.deps import RBACChecker, User

        user = User(
            id="user123",
            username="testuser",
            email="test@example.com",
            role="content_admin"
        )

        checker = RBACChecker(["projects:create"])
        result = checker(user)
        assert result == user

    def test_rbac_checker_denies_permission(self):
        """Test RBACChecker denies access without permission."""
        from api.deps import RBACChecker, User

        user = User(
            id="user123",
            username="testuser",
            email="test@example.com",
            role="viewer"
        )

        checker = RBACChecker(["chapters:create"])

        with pytest.raises(HTTPException) as exc_info:
            checker(user)

        assert exc_info.value.status_code == 403
        assert "PERMISSION_DENIED" in str(exc_info.value.detail)

    def test_rbac_checker_system_admin_bypasses(self):
        """Test system_admin bypasses permission check."""
        from api.deps import RBACChecker, User

        user = User(
            id="user123",
            username="testuser",
            email="test@example.com",
            role="system_admin"
        )

        checker = RBACChecker(["anything:delete"])
        result = checker(user)
        assert result == user


class TestRequirePermission:
    """Test require_permission dependency factory."""

    def test_require_permission_returns_checker(self):
        """Test require_permission returns RBACChecker instance."""
        from api.deps import require_permission

        result = require_permission("chapters:read")
        assert result is not None


class TestRequireRole:
    """Test require_role dependency factory."""

    @pytest.mark.asyncio
    async def test_require_role_returns_dependency(self):
        """Test require_role returns async dependency function."""
        from api.deps import require_role, User

        role_check = require_role("admin", "editor")

        user = User(
            id="user123",
            username="testuser",
            email="test@example.com",
            role="editor"
        )

        result = await role_check(user)
        assert result == user

    @pytest.mark.asyncio
    async def test_require_role_unauthorized(self):
        """Test require_role raises for unauthorized role."""
        from api.deps import require_role, User

        role_check = require_role("admin")

        user = User(
            id="user123",
            username="testuser",
            email="test@example.com",
            role="viewer"
        )

        with pytest.raises(HTTPException) as exc_info:
            await role_check(user)

        assert exc_info.value.status_code == 403


class TestRequireMinRole:
    """Test require_min_role dependency factory."""

    @pytest.mark.asyncio
    async def test_require_min_role_sufficient_level(self):
        """Test require_min_role allows sufficient role level."""
        from api.deps import require_min_role, User

        min_role_check = require_min_role("editor")

        user = User(
            id="user123",
            username="testuser",
            email="test@example.com",
            role="editor"
        )

        result = await min_role_check(user)
        assert result == user

    @pytest.mark.asyncio
    async def test_require_min_role_insufficient_level(self):
        """Test require_min_role denies insufficient role level."""
        from api.deps import require_min_role, User

        min_role_check = require_min_role("editor")

        user = User(
            id="user123",
            username="testuser",
            email="test@example.com",
            role="viewer"
        )

        with pytest.raises(HTTPException) as exc_info:
            await min_role_check(user)

        assert exc_info.value.status_code == 403
        assert "ROLE_LEVEL_TOO_LOW" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_require_min_role_exact_level(self):
        """Test require_min_role allows exact role level."""
        from api.deps import require_min_role, User

        min_role_check = require_min_role("editor")

        user = User(
            id="user123",
            username="testuser",
            email="test@example.com",
            role="editor"
        )

        result = await min_role_check(user)
        assert result == user


class TestGetCurrentUser:
    """Test get_current_user dependency."""

    @pytest.mark.asyncio
    async def test_get_current_user_with_valid_credentials(self):
        """Test get_current_user returns user for valid token."""
        from api.deps import get_current_user, create_access_token

        token = create_access_token({
            "sub": "user123",
            "email": "test@example.com",
            "role": "editor"
        })

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        mock_request = MagicMock()
        mock_request.state = MagicMock()

        result = await get_current_user(mock_request, credentials)
        assert result is not None
        assert result.id == "user123"
        assert result.email == "test@example.com"
        assert result.role == "editor"

    @pytest.mark.asyncio
    async def test_get_current_user_without_credentials(self):
        """Test get_current_user returns None without credentials."""
        from api.deps import get_current_user

        mock_request = MagicMock()
        mock_request.state = MagicMock(spec=[])  # Empty state with no user attribute

        result = await get_current_user(mock_request, None)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_current_user_with_existing_state_user(self):
        """Test get_current_user returns user from request.state if available."""
        from api.deps import get_current_user, User

        user = User(
            id="state_user",
            username="stateuser",
            email="state@example.com",
            role="viewer"
        )

        mock_request = MagicMock()
        mock_request.state = MagicMock()
        mock_request.state.user = user

        result = await get_current_user(mock_request, None)
        assert result == user

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """Test get_current_user raises for invalid token."""
        from api.deps import get_current_user

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid_token")
        mock_request = MagicMock()
        mock_request.state = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, credentials)

        assert exc_info.value.status_code == 401


class TestGetCurrentActiveUser:
    """Test get_current_active_user dependency."""

    @pytest.mark.asyncio
    async def test_get_current_active_user_returns_user(self):
        """Test get_current_active_user returns user when authenticated."""
        from api.deps import get_current_active_user, User

        user = User(
            id="user123",
            username="testuser",
            email="test@example.com",
            role="editor"
        )

        result = await get_current_active_user(user)
        assert result == user

    @pytest.mark.asyncio
    async def test_get_current_active_user_raises_when_none(self):
        """Test get_current_active_user raises when user is None."""
        from api.deps import get_current_active_user

        with pytest.raises(HTTPException) as exc_info:
            await get_current_active_user(None)

        assert exc_info.value.status_code == 401
        assert "UNAUTHORIZED" in str(exc_info.value.detail)


class TestGetOptionalUser:
    """Test get_optional_user dependency."""

    @pytest.mark.asyncio
    async def test_get_optional_user_with_token(self):
        """Test get_optional_user returns user when token provided."""
        from api.deps import get_optional_user, create_access_token

        token = create_access_token({
            "sub": "user123",
            "email": "test@example.com",
            "role": "editor"
        })

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        mock_request = MagicMock()
        mock_request.state = MagicMock()

        result = await get_optional_user(mock_request, credentials)
        assert result is not None
        assert result.id == "user123"

    @pytest.mark.asyncio
    async def test_get_optional_user_without_token(self):
        """Test get_optional_user returns None when no token."""
        from api.deps import get_optional_user

        mock_request = MagicMock()
        mock_request.state = MagicMock(spec=[])  # Empty state with no user attribute

        result = await get_optional_user(mock_request, None)
        assert result is None


class TestDatabaseSession:
    """Test DatabaseSession class."""

    def test_database_session_creation(self):
        """Test DatabaseSession initializes empty."""
        from api.deps import DatabaseSession

        session = DatabaseSession()
        assert session._users == {}
        assert session._projects == {}
        assert session._chapters == {}
        assert session._terms == {}

    def test_create_and_get_user(self):
        """Test DatabaseSession create and get user."""
        from api.deps import DatabaseSession

        session = DatabaseSession()
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "role": "editor"
        }

        created_user = session.create_user(user_data)
        assert created_user.id is not None
        assert created_user.username == "testuser"
        assert created_user.email == "test@example.com"
        assert created_user.role == "editor"

        retrieved = session.get_user_by_email("test@example.com")
        assert retrieved is not None
        assert retrieved.email == "test@example.com"

    def test_get_user_by_id(self):
        """Test DatabaseSession get_user_by_id."""
        from api.deps import DatabaseSession

        session = DatabaseSession()
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "role": "editor"
        }

        created = session.create_user(user_data)
        retrieved = session.get_user_by_id(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id

    def test_get_user_by_email_not_found(self):
        """Test DatabaseSession get_user_by_email returns None when not found."""
        from api.deps import DatabaseSession

        session = DatabaseSession()
        result = session.get_user_by_email("nonexistent@example.com")
        assert result is None

    def test_create_and_get_project(self):
        """Test DatabaseSession create and get project."""
        from api.deps import DatabaseSession

        session = DatabaseSession()
        project_data = {
            "name": "Test Project",
            "description": "A test project",
            "owner_id": "owner123"
        }

        created = session.create_project(project_data)
        assert created["id"] is not None
        assert created["name"] == "Test Project"
        assert created["status"] == "draft"

        retrieved = session.get_project(created["id"])
        assert retrieved is not None
        assert retrieved["name"] == "Test Project"

    def test_list_projects(self):
        """Test DatabaseSession list_projects."""
        from api.deps import DatabaseSession

        session = DatabaseSession()
        session.create_project({"name": "Project 1", "owner_id": "owner1"})
        session.create_project({"name": "Project 2", "owner_id": "owner1"})
        session.create_project({"name": "Project 3", "owner_id": "owner2"})

        all_projects = session.list_projects()
        assert len(all_projects) == 3

        owner1_projects = session.list_projects(owner_id="owner1")
        assert len(owner1_projects) == 2

    def test_update_project(self):
        """Test DatabaseSession update_project."""
        from api.deps import DatabaseSession

        session = DatabaseSession()
        created = session.create_project({"name": "Original Name", "owner_id": "owner1"})

        updated = session.update_project(created["id"], {"name": "Updated Name", "status": "active"})
        assert updated is not None
        assert updated["name"] == "Updated Name"
        assert updated["status"] == "active"

    def test_delete_project(self):
        """Test DatabaseSession delete_project."""
        from api.deps import DatabaseSession

        session = DatabaseSession()
        created = session.create_project({"name": "To Delete", "owner_id": "owner1"})

        result = session.delete_project(created["id"])
        assert result is True

        retrieved = session.get_project(created["id"])
        assert retrieved is None

    def test_create_and_get_chapter(self):
        """Test DatabaseSession create and get chapter."""
        from api.deps import DatabaseSession

        session = DatabaseSession()
        project = session.create_project({"name": "Test Project", "owner_id": "owner1"})

        chapter_data = {
            "project_id": project["id"],
            "title": "Chapter 1",
            "order_num": 1
        }

        created = session.create_chapter(chapter_data)
        assert created["id"] is not None
        assert created["title"] == "Chapter 1"
        assert created["status"] == "draft"

        retrieved = session.get_chapter(created["id"])
        assert retrieved is not None
        assert retrieved["title"] == "Chapter 1"

    def test_list_chapters_by_project(self):
        """Test DatabaseSession list_chapters_by_project."""
        from api.deps import DatabaseSession

        session = DatabaseSession()
        project = session.create_project({"name": "Test Project", "owner_id": "owner1"})

        session.create_chapter({"project_id": project["id"], "title": "Chapter 1", "order_num": 1})
        session.create_chapter({"project_id": project["id"], "title": "Chapter 2", "order_num": 2})
        session.create_chapter({"project_id": "other_project", "title": "Chapter 3", "order_num": 1})

        chapters = session.list_chapters_by_project(project["id"])
        assert len(chapters) == 2

    def test_update_chapter(self):
        """Test DatabaseSession update_chapter."""
        from api.deps import DatabaseSession

        session = DatabaseSession()
        project = session.create_project({"name": "Test Project", "owner_id": "owner1"})
        created = session.create_chapter({"project_id": project["id"], "title": "Original", "order_num": 1})

        updated = session.update_chapter(created["id"], {"title": "Updated", "status": "published"})
        assert updated is not None
        assert updated["title"] == "Updated"
        assert updated["status"] == "published"

    def test_delete_chapter(self):
        """Test DatabaseSession delete_chapter."""
        from api.deps import DatabaseSession

        session = DatabaseSession()
        project = session.create_project({"name": "Test Project", "owner_id": "owner1"})
        created = session.create_chapter({"project_id": project["id"], "title": "To Delete", "order_num": 1})

        result = session.delete_chapter(created["id"])
        assert result is True

        retrieved = session.get_chapter(created["id"])
        assert retrieved is None

    def test_create_and_get_term(self):
        """Test DatabaseSession create and get term."""
        from api.deps import DatabaseSession

        session = DatabaseSession()
        term_data = {
            "term": "TestTerm",
            "definition": "A test term definition",
            "domain": "testing"
        }

        created = session.create_term(term_data)
        assert created["id"] is not None
        assert created["term"] == "TestTerm"
        assert created["locked"] is False

        retrieved = session.get_term(created["id"])
        assert retrieved is not None
        assert retrieved["term"] == "TestTerm"

    def test_list_terms(self):
        """Test DatabaseSession list_terms."""
        from api.deps import DatabaseSession

        session = DatabaseSession()
        session.create_term({"term": "Term1", "definition": "Def1", "domain": "domain1"})
        session.create_term({"term": "Term2", "definition": "Def2", "domain": "domain1"})
        session.create_term({"term": "Term3", "definition": "Def3", "domain": "domain2"})

        all_terms = session.list_terms()
        assert len(all_terms) == 3

        domain1_terms = session.list_terms(domain="domain1")
        assert len(domain1_terms) == 2

    def test_update_term(self):
        """Test DatabaseSession update_term."""
        from api.deps import DatabaseSession

        session = DatabaseSession()
        created = session.create_term({"term": "Original", "definition": "Original def", "domain": "test"})

        updated = session.update_term(created["id"], {"term": "Updated", "definition": "Updated def"})
        assert updated is not None
        assert updated["term"] == "Updated"
        assert updated["definition"] == "Updated def"

    def test_delete_term(self):
        """Test DatabaseSession delete_term."""
        from api.deps import DatabaseSession

        session = DatabaseSession()
        created = session.create_term({"term": "To Delete", "definition": "Def", "domain": "test"})

        result = session.delete_term(created["id"])
        assert result is True

        retrieved = session.get_term(created["id"])
        assert retrieved is None

    def test_lock_term(self):
        """Test DatabaseSession lock_term."""
        from api.deps import DatabaseSession

        session = DatabaseSession()
        created = session.create_term({"term": "Lockable", "definition": "Def", "domain": "test"})

        locked = session.lock_term(created["id"], "Content dispute")
        assert locked is not None
        assert locked["locked"] is True
        assert locked["lock_reason"] == "Content dispute"

    def test_sessions(self):
        """Test DatabaseSession session management."""
        from api.deps import DatabaseSession

        session = DatabaseSession()
        session.add_session("user123", "token_abc")
        session.add_session("user456", "token_def")

        assert session.get_session("token_abc") == "user123"
        assert session.get_session("token_def") == "user456"
        assert session.get_session("nonexistent") is None


class TestGetDB:
    """Test get_db dependency."""

    @pytest.mark.asyncio
    async def test_get_db_returns_singleton(self):
        """Test get_db returns the singleton database session."""
        from api.deps import get_db, db_session

        result = await get_db()
        assert result is db_session


class TestDecodeTokenEdgeCases:
    """Test decode_token edge cases."""

    def test_decode_token_wrong_type_raises_jwt_error(self):
        """Test decode_token raises JWTError when token type mismatch."""
        from api.deps import create_access_token, decode_token, create_refresh_token

        token = create_refresh_token({"sub": "user123", "email": "test@example.com", "role": "viewer"})

        with pytest.raises(HTTPException) as exc_info:
            decode_token(token, "access")

        assert exc_info.value.status_code == 401
        assert "TOKEN_INVALID" in str(exc_info.value.detail)


class TestGetCurrentUserEdgeCases:
    """Test get_current_user edge cases."""

    @pytest.mark.asyncio
    async def test_get_current_user_generic_exception(self):
        """Test get_current_user raises 401 on unexpected exception."""
        from api.deps import get_current_user
        from unittest.mock import MagicMock
        from fastapi.security import HTTPAuthorizationCredentials
        from jose import jwt

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid_format_but_invalid")

        mock_request = MagicMock()
        mock_request.state = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, credentials)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_decode_error(self):
        """Test get_current_user handles decode errors properly."""
        from api.deps import get_current_user
        from fastapi.security import HTTPAuthorizationCredentials

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="malformed.token.here")
        mock_request = MagicMock()
        mock_request.state = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, credentials)

        assert exc_info.value.status_code == 401


class TestRequireMinRoleEdgeCases:
    """Test require_min_role edge cases."""

    @pytest.mark.asyncio
    async def test_require_min_role_unauthorized(self):
        """Test require_min_role raises when user is None."""
        from api.deps import require_min_role

        min_role_check = require_min_role("editor")

        with pytest.raises(HTTPException) as exc_info:
            await min_role_check(None)

        assert exc_info.value.status_code == 401
        assert "UNAUTHORIZED" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_require_min_role_level_too_low(self):
        """Test require_min_role raises when role level is insufficient."""
        from api.deps import require_min_role, User

        min_role_check = require_min_role("editor")

        user = User(
            id="user123",
            username="testuser",
            email="test@example.com",
            role="viewer"
        )

        with pytest.raises(HTTPException) as exc_info:
            await min_role_check(user)

        assert exc_info.value.status_code == 403
        assert "ROLE_LEVEL_TOO_LOW" in str(exc_info.value.detail)


class TestDatabaseSessionEdgeCases:
    """Test DatabaseSession edge cases for not-found scenarios."""

    def test_get_project_not_found(self):
        """Test get_project returns None when project doesn't exist."""
        from api.deps import DatabaseSession

        session = DatabaseSession()
        result = session.get_project("nonexistent_id")
        assert result is None

    def test_delete_project_not_found(self):
        """Test delete_project returns False when project doesn't exist."""
        from api.deps import DatabaseSession

        session = DatabaseSession()
        result = session.delete_project("nonexistent_id")
        assert result is False

    def test_get_chapter_not_found(self):
        """Test get_chapter returns None when chapter doesn't exist."""
        from api.deps import DatabaseSession

        session = DatabaseSession()
        result = session.get_chapter("nonexistent_id")
        assert result is None

    def test_delete_chapter_not_found(self):
        """Test delete_chapter returns False when chapter doesn't exist."""
        from api.deps import DatabaseSession

        session = DatabaseSession()
        result = session.delete_chapter("nonexistent_id")
        assert result is False

    def test_get_term_not_found(self):
        """Test get_term returns None when term doesn't exist."""
        from api.deps import DatabaseSession

        session = DatabaseSession()
        result = session.get_term("nonexistent_id")
        assert result is None

    def test_delete_term_not_found(self):
        """Test delete_term returns False when term doesn't exist."""
        from api.deps import DatabaseSession

        session = DatabaseSession()
        result = session.delete_term("nonexistent_id")
        assert result is False

    def test_lock_term_not_found(self):
        """Test lock_term returns None when term doesn't exist."""
        from api.deps import DatabaseSession

        session = DatabaseSession()
        result = session.lock_term("nonexistent_id", "test reason")
        assert result is None

    def test_update_project_not_found(self):
        """Test update_project returns None when project doesn't exist."""
        from api.deps import DatabaseSession

        session = DatabaseSession()
        result = session.update_project("nonexistent_id", {"name": "New Name"})
        assert result is None

    def test_update_chapter_not_found(self):
        """Test update_chapter returns None when chapter doesn't exist."""
        from api.deps import DatabaseSession

        session = DatabaseSession()
        result = session.update_chapter("nonexistent_id", {"title": "New Title"})
        assert result is None

    def test_update_term_not_found(self):
        """Test update_term returns None when term doesn't exist."""
        from api.deps import DatabaseSession

        session = DatabaseSession()
        result = session.update_term("nonexistent_id", {"term": "New Term"})
        assert result is None

    def test_create_chapter_with_parent(self):
        """Test create_chapter with parent_chapter_id."""
        from api.deps import DatabaseSession

        session = DatabaseSession()
        project = session.create_project({"name": "Test Project", "owner_id": "owner1"})
        parent = session.create_chapter({"project_id": project["id"], "title": "Parent", "order_num": 1})

        child = session.create_chapter({
            "project_id": project["id"],
            "title": "Child Chapter",
            "order_num": 2,
            "parent_chapter_id": parent["id"]
        })

        assert child["parent_chapter_id"] == parent["id"]

    def test_delete_project_returns_false_when_not_found(self):
        """Test delete_project returns False for non-existent project."""
        from api.deps import DatabaseSession

        session = DatabaseSession()
        result = session.delete_project("fake-id")
        assert result is False

    def test_delete_chapter_returns_false_when_not_found(self):
        """Test delete_chapter returns False for non-existent chapter."""
        from api.deps import DatabaseSession

        session = DatabaseSession()
        result = session.delete_chapter("fake-id")
        assert result is False

    def test_delete_term_returns_false_when_not_found(self):
        """Test delete_term returns False for non-existent term."""
        from api.deps import DatabaseSession

        session = DatabaseSession()
        result = session.delete_term("fake-id")
        assert result is False


class TestRBACCheckerEdgeCases:
    """Test RBACChecker edge cases."""

    def test_rbac_checker_with_none_user(self):
        """Test RBACChecker raises when user is None (directly called)."""
        from api.deps import RBACChecker

        checker = RBACChecker(["chapters:read"])

        with pytest.raises(HTTPException) as exc_info:
            checker(None)

        assert exc_info.value.status_code == 401

    def test_rbac_checker_direct_call_with_user(self):
        """Test RBACChecker allows access when called directly with valid user."""
        from api.deps import RBACChecker, User

        user = User(
            id="user123",
            username="testuser",
            email="test@example.com",
            role="editor"
        )

        checker = RBACChecker(["chapters:create"])
        result = checker(user)
        assert result == user


class TestRequireRoleEdgeCases:
    """Test require_role edge cases."""

    @pytest.mark.asyncio
    async def test_require_role_raises_when_user_none(self):
        """Test require_role raises when user is None (dependency injection)."""
        from api.deps import require_role

        role_check = require_role("editor", "admin")

        with pytest.raises(HTTPException) as exc_info:
            await role_check(None)

        assert exc_info.value.status_code == 401


class TestRequireMinRoleNoneUser:
    """Test require_min_role with None user edge case."""

    @pytest.mark.asyncio
    async def test_require_min_role_raises_when_user_none(self):
        """Test require_min_role raises when user is None (dependency injection)."""
        from api.deps import require_min_role

        min_role_check = require_min_role("editor")

        with pytest.raises(HTTPException) as exc_info:
            await min_role_check(None)

        assert exc_info.value.status_code == 401


class TestDecodeTokenTypeMismatch:
    """Test decode_token type mismatch edge cases."""

    def test_decode_token_access_as_refresh_raises(self):
        """Test decode_token raises when access token used as refresh."""
        from api.deps import create_access_token, decode_token

        access_token = create_access_token({
            "sub": "user123",
            "email": "test@example.com",
            "role": "viewer"
        })

        with pytest.raises(HTTPException) as exc_info:
            decode_token(access_token, "refresh")

        assert exc_info.value.status_code == 401
        assert "TOKEN_INVALID" in str(exc_info.value.detail)

    def test_decode_token_refresh_as_access_raises(self):
        """Test decode_token raises when refresh token used as access."""
        from api.deps import create_refresh_token, decode_token

        refresh_token = create_refresh_token({
            "sub": "user123",
            "email": "test@example.com",
            "role": "viewer"
        })

        with pytest.raises(HTTPException) as exc_info:
            decode_token(refresh_token, "access")

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_handles_non_jwt_exception(self):
        """Test get_current_user handles unexpected non-JWTError exceptions."""
        from api.deps import get_current_user, create_access_token
        from fastapi.security import HTTPAuthorizationCredentials
        from unittest.mock import patch

        token = create_access_token({
            "sub": "user123",
            "email": "test@example.com",
            "role": "viewer"
        })

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        mock_request = MagicMock()
        mock_request.state = MagicMock()

        with patch('api.deps.jwt.decode') as mock_decode:
            mock_decode.side_effect = ValueError("Unexpected error during decode")

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_request, credentials)

            assert exc_info.value.status_code == 401
            assert "TOKEN_INVALID" in str(exc_info.value.detail)


class TestDecodeTokenInvalidType:
    """Test decode_token with invalid/missing type field."""

    def test_decode_token_missing_type_field(self):
        """Test decode_token raises when token has no type field."""
        from api.deps import decode_token, SECRET_KEY, ALGORITHM
        from jose import jwt

        payload = {
            "sub": "user123",
            "email": "test@example.com",
            "role": "viewer",
            "exp": 9999999999,
            "iat": 1234567890
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

        with pytest.raises(HTTPException) as exc_info:
            decode_token(token, "access")

        assert exc_info.value.status_code == 401
        assert "TOKEN_INVALID" in str(exc_info.value.detail)
        assert "Invalid token type" in str(exc_info.value.detail)
