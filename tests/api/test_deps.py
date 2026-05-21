"""
Unit Tests for API Dependencies and Utilities

Tests for:
- Password hashing and verification
- JWT token creation and decoding
- Role-based access control (RBAC)
- Database session operations
- Utility functions
"""

from datetime import timedelta

import pytest
from api.deps import (
    ROLE_HIERARCHY,
    ROLE_PERMISSIONS,
    DatabaseSession,
    RBACChecker,
    TokenData,
    User,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_uuid,
    get_password_hash,
    hash_content,
    require_permission,
    require_role,
    verify_password,
)
from fastapi import HTTPException


class TestPasswordHashing:
    """Tests for password hashing functions"""

    def test_get_password_hash_returns_string(self):
        """Test that get_password_hash returns a hash string"""
        password = "testpassword123"
        hashed = get_password_hash(password)

        assert isinstance(hashed, str)
        assert hashed != password
        assert len(hashed) > 0

    def test_get_password_hash_different_for_same_password(self):
        """Test that hashing same password twice gives different results (salt)"""
        password = "testpassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Test verify_password with correct password"""
        password = "testpassword123"
        hashed = get_password_hash(password)

        result = verify_password(password, hashed)
        assert result is True

    def test_verify_password_incorrect(self):
        """Test verify_password with incorrect password"""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = get_password_hash(password)

        result = verify_password(wrong_password, hashed)
        assert result is False

    def test_verify_password_empty_strings(self):
        """Test verify_password with empty strings raises exception"""
        with pytest.raises(Exception):
            verify_password("", "")


class TestJWTTokens:
    """Tests for JWT token creation and decoding"""

    def test_create_access_token_returns_string(self):
        """Test that create_access_token returns a JWT string"""
        data = {"sub": "user123", "email": "test@test.com", "role": "viewer"}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0
        assert token.count(".") == 2

    def test_create_access_token_with_custom_expiry(self):
        """Test create_access_token with custom expiry time"""
        data = {"sub": "user123", "email": "test@test.com", "role": "viewer"}
        expires = timedelta(minutes=5)
        token = create_access_token(data, expires_delta=expires)

        assert isinstance(token, str)

    def test_decode_access_token_valid(self):
        """Test decoding a valid access token"""
        data = {"sub": "user123", "email": "test@test.com", "role": "viewer"}
        token = create_access_token(data)

        token_data = decode_token(token, "access")

        assert isinstance(token_data, TokenData)
        assert token_data.sub == "user123"
        assert token_data.email == "test@test.com"
        assert token_data.role == "viewer"
        assert token_data.type == "access"

    def test_decode_token_invalid_format(self):
        """Test decoding token with invalid format"""
        with pytest.raises(HTTPException) as exc_info:
            decode_token("invalid.token", "access")

        assert exc_info.value.status_code == 401

    def test_decode_token_wrong_type(self):
        """Test decoding token with wrong type"""
        data = {"sub": "user123", "email": "test@test.com", "role": "viewer"}
        token = create_access_token(data)

        with pytest.raises(HTTPException) as exc_info:
            decode_token(token, "refresh")

        assert exc_info.value.status_code == 401

    def test_create_refresh_token_returns_string(self):
        """Test that create_refresh_token returns a JWT string"""
        data = {"sub": "user123", "email": "test@test.com", "role": "viewer"}
        token = create_refresh_token(data)

        assert isinstance(token, str)
        assert len(token) > 0
        assert token.count(".") == 2

    def test_decode_refresh_token_valid(self):
        """Test decoding a valid refresh token"""
        data = {"sub": "user123", "email": "test@test.com", "role": "viewer"}
        token = create_refresh_token(data)

        token_data = decode_token(token, "refresh")

        assert isinstance(token_data, TokenData)
        assert token_data.sub == "user123"
        assert token_data.type == "refresh"


class TestRoleHierarchy:
    """Tests for role hierarchy"""

    def test_role_hierarchy_values(self):
        """Test that role hierarchy has correct values"""
        assert ROLE_HIERARCHY["system_admin"] == 6
        assert ROLE_HIERARCHY["content_admin"] == 5
        assert ROLE_HIERARCHY["editor"] == 4
        assert ROLE_HIERARCHY["reviewer"] == 3
        assert ROLE_HIERARCHY["author"] == 2
        assert ROLE_HIERARCHY["viewer"] == 1

    def test_role_hierarchy_system_admin_highest(self):
        """Test that system_admin has highest role level"""
        assert ROLE_HIERARCHY["system_admin"] > ROLE_HIERARCHY["content_admin"]
        assert ROLE_HIERARCHY["system_admin"] > ROLE_HIERARCHY["editor"]


class TestRolePermissions:
    """Tests for role permissions"""

    def test_system_admin_has_wildcard_permission(self):
        """Test that system_admin has *:* permission"""
        assert "*:*" in ROLE_PERMISSIONS["system_admin"]

    def test_content_admin_has_correct_permissions(self):
        """Test content_admin permissions"""
        perms = ROLE_PERMISSIONS["content_admin"]
        assert "projects:*" in perms
        assert "chapters:*" in perms
        assert "terms:*" in perms
        assert "knowledge_graph:*" in perms
        assert "security:*" in perms
        assert "monitor:*" in perms

    def test_editor_permissions(self):
        """Test editor permissions"""
        perms = ROLE_PERMISSIONS["editor"]
        assert "projects:read" in perms
        assert "chapters:*" in perms
        assert "terms:*" in perms
        assert "knowledge_graph:read" in perms
        assert "knowledge_graph:create" in perms

    def test_viewer_permissions(self):
        """Test viewer permissions (read-only)"""
        perms = ROLE_PERMISSIONS["viewer"]
        assert "projects:read" in perms
        assert "chapters:read" in perms
        assert "terms:read" in perms
        assert len(perms) == 4


class TestRBACChecker:
    """Tests for RBAC checker"""

    def test_rbac_checker_wildcard_permission(self):
        """Test that *:* permission grants access to any resource"""
        checker = RBACChecker(["projects:create"])
        user = User(
            id="admin1",
            username="admin",
            email="admin@test.com",
            role="system_admin",
            organization_id="org1",
            clearance_level=5,
        )

        result = checker(user)
        assert result == user

    def test_rbac_checker_specific_permission_granted(self):
        """Test that specific permission grants access"""
        checker = RBACChecker(["projects:read"])
        user = User(
            id="user1",
            username="user",
            email="user@test.com",
            role="viewer",
            organization_id="org1",
            clearance_level=1,
        )

        result = checker(user)
        assert result == user

    def test_rbac_checker_specific_permission_denied(self):
        """Test that missing permission raises HTTPException"""
        checker = RBACChecker(["monitor:read"])
        user = User(
            id="user1",
            username="user",
            email="user@test.com",
            role="viewer",
            organization_id="org1",
            clearance_level=1,
        )

        with pytest.raises(HTTPException) as exc_info:
            checker(user)

        assert exc_info.value.status_code == 403

    def test_rbac_checker_multiple_permissions_some_denied(self):
        """Test RBAC with multiple required permissions where one is denied"""
        checker = RBACChecker(["projects:read", "monitor:logs"])
        user = User(
            id="user1",
            username="user",
            email="user@test.com",
            role="viewer",
            organization_id="org1",
            clearance_level=1,
        )

        with pytest.raises(HTTPException) as exc_info:
            checker(user)

        assert exc_info.value.status_code == 403


class TestRequirePermission:
    """Tests for require_permission dependency factory"""

    def test_require_permission_returns_checker(self):
        """Test that require_permission returns RBACChecker"""
        result = require_permission("projects:read")
        assert isinstance(result, RBACChecker)


class TestRequireRole:
    """Tests for require_role dependency factory"""

    def test_require_role_returns_async_dependency(self):
        """Test that require_role returns an async dependency function"""
        result = require_role("admin")
        assert callable(result)


class TestDatabaseSession:
    """Tests for DatabaseSession"""

    def test_create_user(self):
        """Test creating a user in database session"""
        db = DatabaseSession()
        user_data = {
            "username": "testuser",
            "email": "test@test.com",
            "password": "testpassword123",
            "role": "viewer",
            "organization_id": "org1",
            "clearance_level": 1,
        }

        user = db.create_user(user_data)

        assert isinstance(user, User)
        assert user.username == "testuser"
        assert user.email == "test@test.com"
        assert user.role == "viewer"
        assert user.id is not None

    def test_get_user_by_email(self):
        """Test retrieving user by email"""
        db = DatabaseSession()
        user_data = {
            "username": "testuser",
            "email": "test@test.com",
            "password": "testpassword123",
            "role": "viewer",
        }

        created_user = db.create_user(user_data)
        retrieved_user = db.get_user_by_email("test@test.com")

        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
        assert retrieved_user.email == "test@test.com"

    def test_get_user_by_email_not_found(self):
        """Test retrieving non-existent user by email"""
        db = DatabaseSession()

        result = db.get_user_by_email("nonexistent@test.com")

        assert result is None

    def test_get_user_by_id(self):
        """Test retrieving user by ID"""
        db = DatabaseSession()
        user_data = {
            "username": "testuser",
            "email": "test@test.com",
            "password": "testpassword123",
            "role": "viewer",
        }

        created_user = db.create_user(user_data)
        retrieved_user = db.get_user_by_id(created_user.id)

        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id

    def test_get_user_by_id_not_found(self):
        """Test retrieving non-existent user by ID"""
        db = DatabaseSession()

        result = db.get_user_by_id("nonexistent-id")

        assert result is None

    def test_create_project(self):
        """Test creating a project"""
        db = DatabaseSession()
        project_data = {
            "name": "Test Project",
            "description": "A test project",
            "owner_id": "owner123",
        }

        project = db.create_project(project_data)

        assert project["name"] == "Test Project"
        assert project["description"] == "A test project"
        assert project["owner_id"] == "owner123"
        assert project["id"] is not None
        assert project["status"] == "draft"

    def test_get_project(self):
        """Test retrieving a project"""
        db = DatabaseSession()
        project_data = {
            "name": "Test Project",
            "owner_id": "owner123",
        }

        created = db.create_project(project_data)
        retrieved = db.get_project(created["id"])

        assert retrieved is not None
        assert retrieved["id"] == created["id"]

    def test_get_project_not_found(self):
        """Test retrieving non-existent project"""
        db = DatabaseSession()

        result = db.get_project("nonexistent-id")

        assert result is None

    def test_list_projects(self):
        """Test listing projects"""
        db = DatabaseSession()
        db.create_project({"name": "Project 1", "owner_id": "user1"})
        db.create_project({"name": "Project 2", "owner_id": "user1"})
        db.create_project({"name": "Project 3", "owner_id": "user2"})

        all_projects = db.list_projects()
        assert len(all_projects) == 3

        user1_projects = db.list_projects(owner_id="user1")
        assert len(user1_projects) == 2

    def test_update_project(self):
        """Test updating a project"""
        db = DatabaseSession()
        project = db.create_project({"name": "Original", "owner_id": "owner1"})

        updated = db.update_project(project["id"], {"name": "Updated", "status": "active"})

        assert updated is not None
        assert updated["name"] == "Updated"
        assert updated["status"] == "active"

    def test_update_project_not_found(self):
        """Test updating non-existent project"""
        db = DatabaseSession()

        result = db.update_project("nonexistent-id", {"name": "Updated"})

        assert result is None

    def test_delete_project(self):
        """Test deleting a project"""
        db = DatabaseSession()
        project = db.create_project({"name": "To Delete", "owner_id": "owner1"})

        result = db.delete_project(project["id"])

        assert result is True
        assert db.get_project(project["id"]) is None

    def test_delete_project_not_found(self):
        """Test deleting non-existent project"""
        db = DatabaseSession()

        result = db.delete_project("nonexistent-id")

        assert result is False

    def test_create_chapter(self):
        """Test creating a chapter"""
        db = DatabaseSession()
        project = db.create_project({"name": "Test Project", "owner_id": "owner1"})
        chapter_data = {
            "project_id": project["id"],
            "title": "Chapter 1",
            "order_num": 1,
        }

        chapter = db.create_chapter(chapter_data)

        assert chapter["title"] == "Chapter 1"
        assert chapter["project_id"] == project["id"]
        assert chapter["order_num"] == 1
        assert chapter["status"] == "draft"

    def test_get_chapter(self):
        """Test retrieving a chapter"""
        db = DatabaseSession()
        project = db.create_project({"name": "Test Project", "owner_id": "owner1"})
        chapter = db.create_chapter({"project_id": project["id"], "title": "Test", "order_num": 1})

        retrieved = db.get_chapter(chapter["id"])

        assert retrieved is not None
        assert retrieved["id"] == chapter["id"]

    def test_list_chapters_by_project(self):
        """Test listing chapters by project"""
        db = DatabaseSession()
        project1 = db.create_project({"name": "Project 1", "owner_id": "owner1"})
        project2 = db.create_project({"name": "Project 2", "owner_id": "owner1"})

        db.create_chapter({"project_id": project1["id"], "title": "Ch1", "order_num": 1})
        db.create_chapter({"project_id": project1["id"], "title": "Ch2", "order_num": 2})
        db.create_chapter({"project_id": project2["id"], "title": "Ch3", "order_num": 1})

        project1_chapters = db.list_chapters_by_project(project1["id"])
        assert len(project1_chapters) == 2

    def test_update_chapter(self):
        """Test updating a chapter"""
        db = DatabaseSession()
        project = db.create_project({"name": "Test Project", "owner_id": "owner1"})
        chapter = db.create_chapter({"project_id": project["id"], "title": "Original", "order_num": 1})

        updated = db.update_chapter(chapter["id"], {"title": "Updated", "word_count": 100})

        assert updated is not None
        assert updated["title"] == "Updated"
        assert updated["word_count"] == 100

    def test_delete_chapter(self):
        """Test deleting a chapter"""
        db = DatabaseSession()
        project = db.create_project({"name": "Test Project", "owner_id": "owner1"})
        chapter = db.create_chapter({"project_id": project["id"], "title": "To Delete", "order_num": 1})

        result = db.delete_chapter(chapter["id"])

        assert result is True
        assert db.get_chapter(chapter["id"]) is None

    def test_create_term(self):
        """Test creating a term"""
        db = DatabaseSession()
        term_data = {
            "term": "Test Term",
            "definition": "A test definition",
            "domain": "testing",
        }

        term = db.create_term(term_data)

        assert term["term"] == "Test Term"
        assert term["definition"] == "A test definition"
        assert term["domain"] == "testing"
        assert term["locked"] is False
        assert term["version"] == 1

    def test_get_term(self):
        """Test retrieving a term"""
        db = DatabaseSession()
        term = db.create_term({"term": "Test", "definition": "Def"})

        retrieved = db.get_term(term["id"])

        assert retrieved is not None
        assert retrieved["id"] == term["id"]

    def test_list_terms(self):
        """Test listing terms"""
        db = DatabaseSession()
        db.create_term({"term": "Term 1", "definition": "Def 1"})
        db.create_term({"term": "Term 2", "definition": "Def 2"})

        terms = db.list_terms()

        assert len(terms) == 2

    def test_update_term(self):
        """Test updating a term"""
        db = DatabaseSession()
        term = db.create_term({"term": "Original", "definition": "Original def"})

        updated = db.update_term(term["id"], {"term": "Updated", "locked": True})

        assert updated is not None
        assert updated["term"] == "Updated"
        assert updated["locked"] is True

    def test_delete_term(self):
        """Test deleting a term"""
        db = DatabaseSession()
        term = db.create_term({"term": "To Delete", "definition": "Def"})

        result = db.delete_term(term["id"])

        assert result is True
        assert db.get_term(term["id"]) is None


class TestUtilityFunctions:
    """Tests for utility functions"""

    def test_generate_uuid(self):
        """Test generating UUID"""
        uuid1 = generate_uuid()
        uuid2 = generate_uuid()

        assert isinstance(uuid1, str)
        assert len(uuid1) == 36
        assert uuid1 != uuid2

    def test_hash_content(self):
        """Test hashing content"""
        content = "Test content"
        hash1 = hash_content(content)
        hash2 = hash_content(content)

        assert isinstance(hash1, str)
        assert len(hash1) == 64
        assert hash1 == hash2

    def test_hash_content_different_inputs(self):
        """Test that different content produces different hashes"""
        hash1 = hash_content("content 1")
        hash2 = hash_content("content 2")

        assert hash1 != hash2


class TestRBACCheckerWildcardResource:
    """Tests for RBACChecker wildcard resource permissions"""

    def test_rbac_checker_resource_wildcard_permission(self):
        """Test that resource:* permission grants access"""
        checker = RBACChecker(["chapters:create"])
        user = User(
            id="user1",
            username="user",
            email="user@test.com",
            role="editor",
            organization_id="org1",
            clearance_level=1,
        )

        result = checker(user)
        assert result == user

    def test_rbac_checker_resource_specific_permission_denied(self):
        """Test that specific resource permission is denied when not in role"""
        checker = RBACChecker(["monitor:logs"])
        user = User(
            id="user1",
            username="user",
            email="user@test.com",
            role="viewer",
            organization_id="org1",
            clearance_level=1,
        )

        with pytest.raises(HTTPException) as exc_info:
            checker(user)

        assert exc_info.value.status_code == 403


class TestDatabaseSessionExtended:
    """Extended tests for DatabaseSession"""

    def test_lock_term(self):
        """Test locking a term"""
        db = DatabaseSession()
        term = db.create_term(
            {
                "term": "Test Term",
                "definition": "A test definition",
            }
        )

        locked = db.lock_term(term["id"], "Pending review")

        assert locked is not None
        assert locked["locked"] is True
        assert locked["lock_reason"] == "Pending review"

    def test_lock_term_not_found(self):
        """Test locking non-existent term"""
        db = DatabaseSession()

        result = db.lock_term("nonexistent-id", "reason")

        assert result is None

    def test_add_session(self):
        """Test adding a session"""
        db = DatabaseSession()
        user = db.create_user(
            {
                "username": "testuser",
                "email": "test@test.com",
                "password": "testpassword123",
                "role": "viewer",
            }
        )

        db.add_session(user.id, "token123")

        session_user = db.get_session("token123")
        assert session_user == user.id

    def test_get_session_not_found(self):
        """Test getting non-existent session"""
        db = DatabaseSession()

        result = db.get_session("nonexistent-token")

        assert result is None
