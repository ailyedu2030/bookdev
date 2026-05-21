"""Tests for api/routes/admin.py"""

import asyncio
import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from api.deps import DatabaseSession, User


def run_async(coro):
    """Run async coroutine synchronously for testing."""
    return asyncio.get_event_loop().run_until_complete(coro)


class TestListUsers:
    """Test list users endpoint."""

    def test_list_users_success(self):
        """Test successful user listing."""
        from api.routes.admin import list_users

        mock_user = User(
            id="admin-123",
            username="admin",
            email="admin@example.com",
            role="system_admin",
        )

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db._users = {
            "u1": MagicMock(id="u1", username="user1", email="u1@example.com", role="editor", organization_id=None, clearance_level=1),
            "u2": MagicMock(id="u2", username="user2", email="u2@example.com", role="viewer", organization_id=None, clearance_level=1),
        }

        with patch('api.routes.admin.require_role', return_value=lambda u: u):
            result = run_async(list_users(
                page=1, per_page=20, role_filter=None, search=None, user=mock_user, db=mock_db
            ))

            assert len(result) == 2

    def test_list_users_with_role_filter(self):
        """Test user listing with role filter."""
        from api.routes.admin import list_users

        mock_user = User(
            id="admin-123",
            username="admin",
            email="admin@example.com",
            role="system_admin",
        )

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db._users = {
            "u1": MagicMock(id="u1", username="user1", email="u1@example.com", role="editor", organization_id=None, clearance_level=1),
            "u2": MagicMock(id="u2", username="user2", email="u2@example.com", role="editor", organization_id=None, clearance_level=1),
            "u3": MagicMock(id="u3", username="user3", email="u3@example.com", role="viewer", organization_id=None, clearance_level=1),
        }

        with patch('api.routes.admin.require_role', return_value=lambda u: u):
            result = run_async(list_users(
                page=1, per_page=20, role_filter="editor", search=None, user=mock_user, db=mock_db
            ))

            assert len(result) == 2


class TestCreateUser:
    """Test create user endpoint."""

    def test_create_user_success(self):
        """Test successful user creation."""
        from api.routes.admin import create_user
        from api.schemas.auth import UserCreate

        mock_user = User(
            id="admin-123",
            username="admin",
            email="admin@example.com",
            role="system_admin",
        )

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.get_user_by_email.return_value = None
        mock_db.create_user.return_value = MagicMock(
            id="new-user-id",
            username="newuser",
            email="new@example.com",
            role="editor",
            organization_id=None,
            clearance_level=1,
        )

        user_data = UserCreate(
            username="newuser",
            email="new@example.com",
            password="password123",
            role="editor",
        )

        with patch('api.routes.admin.require_role', return_value=lambda u: u):
            with patch('api.routes.admin.get_password_hash', return_value="hashed"):
                result = run_async(create_user(user_data, mock_user, mock_db))

                assert result.username == "newuser"

    def test_create_user_email_exists(self):
        """Test create user fails when email exists."""
        from api.routes.admin import create_user
        from api.schemas.auth import UserCreate

        mock_user = User(
            id="admin-123",
            username="admin",
            email="admin@example.com",
            role="system_admin",
        )

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.get_user_by_email.return_value = MagicMock(id="existing")

        user_data = UserCreate(
            username="newuser",
            email="existing@example.com",
            password="password123",
        )

        with patch('api.routes.admin.require_role', return_value=lambda u: u):
            with pytest.raises(HTTPException) as exc_info:
                run_async(create_user(user_data, mock_user, mock_db))

            assert exc_info.value.status_code == 400
            assert "EMAIL_EXISTS" in str(exc_info.value.detail)


class TestGetUser:
    """Test get user endpoint."""

    def test_get_user_success(self):
        """Test successful user retrieval."""
        from api.routes.admin import get_user

        mock_user = User(
            id="admin-123",
            username="admin",
            email="admin@example.com",
            role="system_admin",
        )

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.get_user_by_id.return_value = MagicMock(
            id="target-456",
            username="target",
            email="target@example.com",
            role="editor",
            organization_id=None,
            clearance_level=1,
        )

        with patch('api.routes.admin.require_role', return_value=lambda u: u):
            result = run_async(get_user("target-456", mock_user, mock_db))

            assert result.id == "target-456"

    def test_get_user_not_found(self):
        """Test get user fails when user doesn't exist."""
        from api.routes.admin import get_user

        mock_user = User(
            id="admin-123",
            username="admin",
            email="admin@example.com",
            role="system_admin",
        )

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.get_user_by_id.return_value = None

        with patch('api.routes.admin.require_role', return_value=lambda u: u):
            with pytest.raises(HTTPException) as exc_info:
                run_async(get_user("nonexistent", mock_user, mock_db))

            assert exc_info.value.status_code == 404


class TestUpdateUser:
    """Test update user endpoint."""

    def test_update_user_success(self):
        """Test successful user update."""
        from api.routes.admin import update_user
        from api.schemas.auth import UserUpdate

        mock_user = User(
            id="admin-123",
            username="admin",
            email="admin@example.com",
            role="system_admin",
        )

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.get_user_by_id.return_value = MagicMock(
            id="target-456",
            username="target",
            email="target@example.com",
            role="editor",
            organization_id=None,
            clearance_level=1,
        )

        update_data = UserUpdate(organization_id="new-org", clearance_level=2)

        with patch('api.routes.admin.require_role', return_value=lambda u: u):
            result = run_async(update_user("target-456", update_data, mock_user, mock_db))

            assert result.clearance_level == 2


class TestDeleteUser:
    """Test delete user endpoint."""

    def test_delete_user_success(self):
        """Test successful user deletion."""
        from api.routes.admin import delete_user

        mock_user = User(
            id="admin-123",
            username="admin",
            email="admin@example.com",
            role="system_admin",
        )

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.get_user_by_id.return_value = MagicMock(id="target-456")
        mock_db._users = {"target-456": MagicMock()}

        with patch('api.routes.admin.require_role', return_value=lambda u: u):
            result = run_async(delete_user("target-456", mock_user, mock_db))

            assert result.success is True

    def test_delete_user_cannot_delete_self(self):
        """Test cannot delete own account."""
        from api.routes.admin import delete_user

        mock_user = User(
            id="admin-123",
            username="admin",
            email="admin@example.com",
            role="system_admin",
        )

        mock_db = MagicMock(spec=DatabaseSession)

        with patch('api.routes.admin.require_role', return_value=lambda u: u):
            with pytest.raises(HTTPException) as exc_info:
                run_async(delete_user("admin-123", mock_user, mock_db))

            assert exc_info.value.status_code == 400
            assert "CANNOT_DELETE_SELF" in str(exc_info.value.detail)


class TestUpdateUserRole:
    """Test update user role endpoint."""

    def test_update_role_success(self):
        """Test successful role update."""
        from api.routes.admin import update_user_role
        from api.schemas.auth import UserRoleUpdate

        mock_user = User(
            id="admin-123",
            username="admin",
            email="admin@example.com",
            role="system_admin",
        )

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.get_user_by_id.return_value = MagicMock(
            id="target-456",
            username="target",
            email="target@example.com",
            role="editor",
            organization_id=None,
            clearance_level=1,
        )

        role_update = UserRoleUpdate(role="reviewer")

        with patch('api.routes.admin.require_role', return_value=lambda u: u):
            result = run_async(update_user_role("target-456", role_update, mock_user, mock_db))

            assert result.role == "reviewer"


class TestGetAdminStats:
    """Test get admin stats endpoint."""

    def test_get_stats_success(self):
        """Test successful stats retrieval."""
        from api.routes.admin import get_admin_stats

        mock_user = User(
            id="admin-123",
            username="admin",
            email="admin@example.com",
            role="system_admin",
        )

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db._users = {"u1": MagicMock(role="editor"), "u2": MagicMock(role="viewer")}
        mock_db._projects = {"p1": {"status": "active"}, "p2": {"status": "draft"}}
        mock_db._chapters = {"c1": {"status": "published"}, "c2": {"status": "draft"}}
        mock_db._terms = {"t1": {}, "t2": {}}

        with patch('api.routes.admin.require_role', return_value=lambda u: u):
            result = run_async(get_admin_stats(mock_user, mock_db))

            assert result["data"]["total_users"] == 2
            assert result["data"]["total_projects"] == 2
            assert result["data"]["total_chapters"] == 2
            assert result["data"]["total_terms"] == 2
