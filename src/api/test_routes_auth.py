"""Tests for api/routes/auth.py"""

import asyncio
import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from api.deps import (
    DatabaseSession,
    User,
    create_access_token,
    create_refresh_token,
    generate_uuid,
    get_password_hash,
)


def run_async(coro):
    """Run async coroutine synchronously for testing."""
    return asyncio.get_event_loop().run_until_complete(coro)


class TestRegister:
    """Test user registration endpoint."""

    def test_register_success(self):
        """Test successful user registration."""
        from api.routes.auth import register
        from api.schemas.auth import UserCreate

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.get_user_by_email.return_value = None
        mock_db.create_user.return_value = MagicMock(
            id="new-user-id",
            username="testuser",
            email="test@example.com",
            role="viewer",
            organization_id=None,
            clearance_level=1,
        )

        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="password123",
            role="viewer",
        )

        result = run_async(register(user_data, mock_db))

        assert result.id == "new-user-id"
        assert result.username == "testuser"
        assert result.email == "test@example.com"

    def test_register_email_exists(self):
        """Test registration fails when email already exists."""
        from api.routes.auth import register
        from api.schemas.auth import UserCreate

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.get_user_by_email.return_value = MagicMock(id="existing-user")

        user_data = UserCreate(
            username="newuser",
            email="existing@example.com",
            password="password123",
        )

        with pytest.raises(HTTPException) as exc_info:
            run_async(register(user_data, mock_db))

        assert exc_info.value.status_code == 400
        assert "EMAIL_EXISTS" in str(exc_info.value.detail)


class TestLogin:
    """Test user login endpoint."""

    def test_login_success(self):
        """Test successful login returns tokens."""
        from api.routes.auth import login
        from api.schemas.auth import UserLogin

        mock_db = MagicMock(spec=DatabaseSession)
        mock_user = MagicMock(
            id="user-123",
            email="test@example.com",
            role="editor",
        )
        mock_db.get_user_by_email.return_value = mock_user
        mock_db.add_session = MagicMock()

        with patch('api.routes.auth.verify_password', return_value=True):
            with patch('api.routes.auth.create_access_token') as mock_access:
                with patch('api.routes.auth.create_refresh_token') as mock_refresh:
                    mock_access.return_value = "access-token-123"
                    mock_refresh.return_value = "refresh-token-123"

                    credentials = UserLogin(email="test@example.com", password="password123")
                    result = run_async(login(credentials, mock_db))

                    assert result.access_token == "access-token-123"
                    assert result.refresh_token == "refresh-token-123"
                    assert result.token_type == "bearer"

    def test_login_user_not_found(self):
        """Test login fails when user doesn't exist."""
        from api.routes.auth import login
        from api.schemas.auth import UserLogin

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.get_user_by_email.return_value = None

        credentials = UserLogin(email="nonexistent@example.com", password="password123")

        with pytest.raises(HTTPException) as exc_info:
            run_async(login(credentials, mock_db))

        assert exc_info.value.status_code == 401
        assert "INVALID_CREDENTIALS" in str(exc_info.value.detail)

    def test_login_wrong_password(self):
        """Test login fails with wrong password."""
        from api.routes.auth import login
        from api.schemas.auth import UserLogin

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.get_user_by_email.return_value = MagicMock(id="user-123")

        with patch('api.routes.auth.verify_password', return_value=False):
            credentials = UserLogin(email="test@example.com", password="wrongpassword")

            with pytest.raises(HTTPException) as exc_info:
                run_async(login(credentials, mock_db))

            assert exc_info.value.status_code == 401


class TestRefreshToken:
    """Test token refresh endpoint."""

    def test_refresh_token_success(self):
        """Test successful token refresh."""
        from api.routes.auth import refresh_token
        from api.schemas.auth import RefreshTokenRequest

        mock_db = MagicMock(spec=DatabaseSession)
        mock_user = MagicMock(
            id="user-123",
            email="test@example.com",
            role="editor",
        )
        mock_db.get_user_by_id.return_value = mock_user

        with patch('api.routes.auth.decode_token') as mock_decode:
            mock_token_data = MagicMock()
            mock_token_data.sub = "user-123"
            mock_decode.return_value = mock_token_data

            with patch('api.routes.auth.create_access_token', return_value="new-access-token"):
                with patch('api.routes.auth.create_refresh_token', return_value="new-refresh-token"):
                    request = RefreshTokenRequest(refresh_token="valid-refresh-token")
                    result = run_async(refresh_token(request, mock_db))

                    assert result.access_token == "new-access-token"
                    assert result.refresh_token == "new-refresh-token"

    def test_refresh_token_user_not_found(self):
        """Test refresh fails when user no longer exists."""
        from api.routes.auth import refresh_token
        from api.schemas.auth import RefreshTokenRequest

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db.get_user_by_id.return_value = None

        with patch('api.routes.auth.decode_token') as mock_decode:
            mock_token_data = MagicMock()
            mock_token_data.sub = "deleted-user"
            mock_decode.return_value = mock_token_data

            request = RefreshTokenRequest(refresh_token="valid-token")

            with pytest.raises(HTTPException) as exc_info:
                run_async(refresh_token(request, mock_db))

            assert exc_info.value.status_code == 401


class TestLogout:
    """Test logout endpoint."""

    def test_logout_success(self):
        """Test successful logout."""
        from api.routes.auth import logout

        mock_request = MagicMock()
        mock_request.headers = {"Authorization": "Bearer valid-token"}

        mock_user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role="editor",
        )

        mock_db = MagicMock(spec=DatabaseSession)
        mock_db._sessions = {"valid-token": "user-123"}

        result = run_async(logout(mock_request, mock_user, mock_db))

        assert result.success is True
        assert "Logged out" in result.message


class TestGetCurrentUser:
    """Test get current user endpoint."""

    def test_get_current_user_success(self):
        """Test successful retrieval of current user."""
        from api.routes.auth import get_current_user_info

        mock_user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role="editor",
            organization_id="org-456",
            clearance_level=2,
        )

        mock_db = MagicMock(spec=DatabaseSession)

        result = run_async(get_current_user_info(mock_user, mock_db))

        assert result.id == "user-123"
        assert result.username == "testuser"
        assert result.email == "test@example.com"
        assert result.role == "editor"


class TestChangePassword:
    """Test password change endpoint."""

    def test_change_password_success(self):
        """Test successful password change."""
        from api.routes.auth import change_password
        from api.schemas.auth import PasswordChange

        mock_user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role="editor",
        )

        mock_db = MagicMock(spec=DatabaseSession)

        with patch('api.routes.auth.get_password_hash', return_value="stored-hash"):
            with patch('api.routes.auth.verify_password', return_value=True):
                password_data = PasswordChange(old_password="oldpass", new_password="newpass123")
                result = run_async(change_password(password_data, mock_user, mock_db))

                assert result.success is True

    def test_change_password_wrong_old(self):
        """Test password change fails with wrong old password."""
        from api.routes.auth import change_password
        from api.schemas.auth import PasswordChange

        mock_user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role="editor",
        )

        mock_db = MagicMock(spec=DatabaseSession)

        with patch('api.routes.auth.get_password_hash', return_value="stored-hash"):
            with patch('api.routes.auth.verify_password', return_value=False):
                password_data = PasswordChange(old_password="wrongold", new_password="newpass123")

                with pytest.raises(HTTPException) as exc_info:
                    run_async(change_password(password_data, mock_user, mock_db))

                assert exc_info.value.status_code == 400
                assert "INCORRECT_PASSWORD" in str(exc_info.value.detail)