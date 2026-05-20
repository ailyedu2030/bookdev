"""
CSRF Middleware Tests

Tests for CSRF protection middleware and token management.
"""

import pytest
import time
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi import HTTPException

from api.middleware.csrf import (
    CSRFTokenManager,
    CSRFMiddleware,
    csrf_protect,
    CSRF_TOKEN_COOKIE_NAME,
    CSRF_TOKEN_HEADER_NAME,
)


class TestCSRFTokenManager:
    """Tests for CSRFTokenManager class"""

    def test_generate_token_returns_string(self):
        """Test token generation returns a string"""
        manager = CSRFTokenManager(secret_key="test-secret")
        token = manager.generate_token()
        assert isinstance(token, str)
        assert len(token) > 0

    def test_generate_token_contains_three_parts(self):
        """Test token has three parts separated by dots"""
        manager = CSRFTokenManager(secret_key="test-secret")
        token = manager.generate_token()
        parts = token.split(".")
        assert len(parts) == 3

    def test_generate_token_different_each_time(self):
        """Test each generated token is unique"""
        manager = CSRFTokenManager(secret_key="test-secret")
        tokens = [manager.generate_token() for _ in range(10)]
        assert len(set(tokens)) == 10

    def test_validate_token_valid_token(self):
        """Test validation of a valid token"""
        manager = CSRFTokenManager(secret_key="test-secret")
        token = manager.generate_token()
        assert manager.validate_token(token) is True

    def test_validate_token_empty_string(self):
        """Test validation rejects empty token"""
        manager = CSRFTokenManager(secret_key="test-secret")
        assert manager.validate_token("") is False

    def test_validate_token_invalid_type(self):
        """Test validation handles non-string input gracefully"""
        manager = CSRFTokenManager(secret_key="test-secret")
        assert manager.validate_token("") is False

    def test_validate_token_wrong_format(self):
        """Test validation rejects malformed token"""
        manager = CSRFTokenManager(secret_key="test-secret")
        assert manager.validate_token("invalid-token") is False
        assert manager.validate_token("a.b") is False
        assert manager.validate_token("a.b.c.d") is False

    def test_validate_token_wrong_signature(self):
        """Test validation rejects token with wrong signature"""
        manager = CSRFTokenManager(secret_key="test-secret")
        token = manager.generate_token()
        parts = token.split(".")
        modified_token = f"{parts[0]}.{parts[1]}.wrongsignature"
        assert manager.validate_token(modified_token) is False

    def test_validate_token_expired(self):
        """Test validation rejects expired token"""
        manager = CSRFTokenManager(secret_key="test-secret")
        token = manager.generate_token()
        parts = token.split(".")
        old_timestamp = int(time.time()) - 7200
        expired_token = f"{parts[0]}.{old_timestamp}.{parts[2]}"
        assert manager.validate_token(expired_token) is False

    def test_validate_token_with_different_secret(self):
        """Test validation fails with different secret key"""
        manager1 = CSRFTokenManager(secret_key="secret1")
        manager2 = CSRFTokenManager(secret_key="secret2")
        token = manager1.generate_token()
        assert manager2.validate_token(token) is False

    def test_sign_token_consistency(self):
        """Test _sign_token produces consistent results"""
        manager = CSRFTokenManager(secret_key="test-secret")
        sig1 = manager._sign_token("token123", 1234567890)
        sig2 = manager._sign_token("token123", 1234567890)
        assert sig1 == sig2
        sig3 = manager._sign_token("token123", 1234567891)
        assert sig1 != sig3

    def test_extract_token_from_header_primary(self):
        """Test extracting token from primary header"""
        manager = CSRFTokenManager()
        mock_request = MagicMock()
        mock_request.headers = {CSRF_TOKEN_HEADER_NAME: "test-token"}
        token = manager.extract_token_from_header(mock_request)
        assert token == "test-token"

    def test_extract_token_from_header_lowercase(self):
        """Test extracting token from lowercase header"""
        manager = CSRFTokenManager()
        mock_request = MagicMock()
        mock_request.headers = {"x-csrf-token": "test-token"}
        token = manager.extract_token_from_header(mock_request)
        assert token == "test-token"

    def test_extract_token_from_header_not_found(self):
        """Test extracting token when header not present"""
        manager = CSRFTokenManager()
        mock_request = MagicMock()
        mock_request.headers = {}
        token = manager.extract_token_from_header(mock_request)
        assert token is None

    def test_extract_token_from_cookie(self):
        """Test extracting token from cookie"""
        manager = CSRFTokenManager()
        mock_request = MagicMock()
        mock_request.cookies = {CSRF_TOKEN_COOKIE_NAME: "cookie-token"}
        token = manager.extract_token_from_cookie(mock_request)
        assert token == "cookie-token"

    def test_extract_token_from_cookie_not_found(self):
        """Test extracting token when cookie not present"""
        manager = CSRFTokenManager()
        mock_request = MagicMock()
        mock_request.cookies = {}
        token = manager.extract_token_from_cookie(mock_request)
        assert token is None


class TestCSRFMiddleware:
    """Tests for CSRFMiddleware class"""

    def test_is_path_safe_with_safe_path(self):
        """Test safe path detection"""
        middleware = CSRFMiddleware(app=MagicMock())
        assert middleware._is_path_safe("/api/monitor/health") is True
        assert middleware._is_path_safe("/docs") is True
        assert middleware._is_path_safe("/openapi.json") is True

    def test_is_path_safe_with_excluded_path(self):
        """Test excluded path detection"""
        middleware = CSRFMiddleware(
            app=MagicMock(),
            exclude_paths=["/api/admin"],
        )
        assert middleware._is_path_safe("/api/admin/users") is True

    def test_is_path_safe_with_unsafe_path(self):
        """Test unsafe path detection"""
        middleware = CSRFMiddleware(app=MagicMock())
        assert middleware._is_path_safe("/api/users") is False
        assert middleware._is_path_safe("/api/projects") is False

    def test_is_state_changing_safe_methods(self):
        """Test state-changing detection for safe methods"""
        middleware = CSRFMiddleware(app=MagicMock())
        assert middleware._is_state_changing("GET") is False
        assert middleware._is_state_changing("HEAD") is False
        assert middleware._is_state_changing("OPTIONS") is False

    def test_is_state_changing_unsafe_methods(self):
        """Test state-changing detection for unsafe methods"""
        middleware = CSRFMiddleware(app=MagicMock())
        assert middleware._is_state_changing("POST") is True
        assert middleware._is_state_changing("PUT") is True
        assert middleware._is_state_changing("PATCH") is True
        assert middleware._is_state_changing("DELETE") is True

    @pytest.mark.asyncio
    async def test_dispatch_safe_path_bypasses(self):
        """Test safe path skips CSRF check"""
        middleware = CSRFMiddleware(app=MagicMock())
        mock_request = MagicMock()
        mock_request.url.path = "/api/monitor/health"
        mock_request.method = "POST"
        call_next = AsyncMock(return_value=MagicMock())
        await middleware.dispatch(mock_request, call_next)
        call_next.assert_called_once()

    @pytest.mark.asyncio
    async def test_dispatch_safe_method_bypasses(self):
        """Test safe method skips CSRF check"""
        middleware = CSRFMiddleware(app=MagicMock())
        mock_request = MagicMock()
        mock_request.url.path = "/api/users"
        mock_request.method = "GET"
        call_next = AsyncMock(return_value=MagicMock())
        await middleware.dispatch(mock_request, call_next)
        call_next.assert_called_once()

    @pytest.mark.asyncio
    async def test_dispatch_missing_cookie_token(self):
        """Test missing cookie token returns 403"""
        middleware = CSRFMiddleware(app=MagicMock())
        mock_request = MagicMock()
        mock_request.url.path = "/api/users"
        mock_request.method = "POST"
        mock_request.headers = {}
        mock_request.cookies = {}
        call_next = AsyncMock(return_value=MagicMock())
        response = await middleware.dispatch(mock_request, call_next)
        assert response.status_code == 403
        call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_dispatch_missing_header_token(self):
        """Test missing header token returns 403"""
        middleware = CSRFMiddleware(app=MagicMock())
        mock_request = MagicMock()
        mock_request.url.path = "/api/users"
        mock_request.method = "POST"
        mock_request.headers = {}
        mock_request.cookies = {"csrf_token": "some-token"}
        call_next = AsyncMock(return_value=MagicMock())
        response = await middleware.dispatch(mock_request, call_next)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_dispatch_invalid_cookie_token(self):
        """Test invalid cookie token returns 403"""
        middleware = CSRFMiddleware(app=MagicMock())
        mock_request = MagicMock()
        mock_request.url.path = "/api/users"
        mock_request.method = "POST"
        mock_request.headers = {"X-CSRF-Token": "header-token"}
        mock_request.cookies = {"csrf_token": "invalid-token"}
        call_next = AsyncMock(return_value=MagicMock())
        response = await middleware.dispatch(mock_request, call_next)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_dispatch_token_mismatch(self):
        """Test tokens mismatch returns 403"""
        manager = CSRFTokenManager(secret_key="test-secret")
        valid_token = manager.generate_token()
        middleware = CSRFMiddleware(app=MagicMock(), token_manager=manager)
        mock_request = MagicMock()
        mock_request.url.path = "/api/users"
        mock_request.method = "POST"
        mock_request.headers = {"X-CSRF-Token": "different-token"}
        mock_request.cookies = {"csrf_token": valid_token}
        call_next = AsyncMock(return_value=MagicMock())
        response = await middleware.dispatch(mock_request, call_next)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_dispatch_valid_token_passes(self):
        """Test valid tokens pass through"""
        manager = CSRFTokenManager(secret_key="test-secret")
        valid_token = manager.generate_token()
        middleware = CSRFMiddleware(app=MagicMock(), token_manager=manager)
        mock_request = MagicMock()
        mock_request.url.path = "/api/users"
        mock_request.method = "POST"
        mock_request.headers = {"X-CSRF-Token": valid_token}
        mock_request.cookies = {"csrf_token": valid_token}
        mock_response = MagicMock()
        call_next = AsyncMock(return_value=mock_response)
        response = await middleware.dispatch(mock_request, call_next)
        assert response == mock_response

    @pytest.mark.asyncio
    async def test_dispatch_sets_cookie_on_state_change(self):
        """Test cookie is set on state-changing request"""
        manager = CSRFTokenManager(secret_key="test-secret")
        valid_token = manager.generate_token()
        middleware = CSRFMiddleware(app=MagicMock(), token_manager=manager)
        mock_request = MagicMock()
        mock_request.url.path = "/api/users"
        mock_request.method = "POST"
        mock_request.headers = {"X-CSRF-Token": valid_token}
        mock_request.cookies = {"csrf_token": valid_token}
        mock_response = MagicMock()
        mock_response.set_cookie = MagicMock()
        call_next = AsyncMock(return_value=mock_response)
        await middleware.dispatch(mock_request, call_next)
        mock_response.set_cookie.assert_called_once()
        call_kwargs = mock_response.set_cookie.call_args
        assert call_kwargs[1]["key"] == CSRF_TOKEN_COOKIE_NAME

    @pytest.mark.asyncio
    async def test_dispatch_does_not_set_cookie_on_safe_method(self):
        """Test cookie is not set on safe method"""
        manager = CSRFTokenManager(secret_key="test-secret")
        middleware = CSRFMiddleware(app=MagicMock(), token_manager=manager)
        mock_request = MagicMock()
        mock_request.url.path = "/api/users"
        mock_request.method = "GET"
        mock_response = MagicMock()
        mock_response.set_cookie = MagicMock()
        call_next = AsyncMock(return_value=mock_response)
        await middleware.dispatch(mock_request, call_next)
        mock_response.set_cookie.assert_not_called()

    def test_custom_safe_paths(self):
        """Test custom safe paths configuration"""
        middleware = CSRFMiddleware(
            app=MagicMock(),
            safe_paths=["/custom/safe", "/another/safe"],
        )
        assert middleware._is_path_safe("/custom/safe/path") is True
        assert middleware._is_path_safe("/another/safe") is True
        assert middleware._is_path_safe("/api/users") is False

    def test_custom_exclude_paths(self):
        """Test custom exclude paths configuration"""
        middleware = CSRFMiddleware(
            app=MagicMock(),
            exclude_paths=["/external/api"],
        )
        assert middleware._is_path_safe("/external/api/endpoint") is True


class TestCSRFProtectDependency:
    """Tests for csrf_protect dependency function"""

    @pytest.mark.asyncio
    async def test_csrf_protect_safe_method_passes(self):
        """Test safe method passes csrf_protect"""
        mock_request = MagicMock()
        mock_request.method = "GET"
        await csrf_protect(mock_request)

    @pytest.mark.asyncio
    async def test_csrf_protect_head_method_passes(self):
        """Test HEAD method passes csrf_protect"""
        mock_request = MagicMock()
        mock_request.method = "HEAD"
        await csrf_protect(mock_request)

    @pytest.mark.asyncio
    async def test_csrf_protect_options_method_passes(self):
        """Test OPTIONS method passes csrf_protect"""
        mock_request = MagicMock()
        mock_request.method = "OPTIONS"
        await csrf_protect(mock_request)

    @pytest.mark.asyncio
    async def test_csrf_protect_missing_tokens_raises(self):
        """Test missing tokens raise HTTPException"""
        mock_request = MagicMock()
        mock_request.method = "POST"
        mock_request.headers = {}
        mock_request.cookies = {}
        with pytest.raises(HTTPException) as exc_info:
            await csrf_protect(mock_request)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_csrf_protect_invalid_token_raises(self):
        """Test invalid token raises HTTPException"""
        mock_request = MagicMock()
        mock_request.method = "POST"
        mock_request.headers = {"X-CSRF-Token": "invalid-token"}
        mock_request.cookies = {"csrf_token": "invalid-token"}
        with pytest.raises(HTTPException) as exc_info:
            await csrf_protect(mock_request)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_csrf_protect_token_mismatch_raises(self):
        """Test token mismatch raises HTTPException"""
        manager = CSRFTokenManager(secret_key="test-secret")
        valid_token = manager.generate_token()
        with patch("api.middleware.csrf.csrf_token_manager", manager):
            mock_request = MagicMock()
            mock_request.method = "POST"
            mock_request.headers = {"X-CSRF-Token": "different-token"}
            mock_request.cookies = {"csrf_token": valid_token}
            with pytest.raises(HTTPException) as exc_info:
                await csrf_protect(mock_request)
            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_csrf_protect_valid_tokens_pass(self):
        """Test valid tokens pass csrf_protect"""
        manager = CSRFTokenManager(secret_key="test-secret")
        valid_token = manager.generate_token()
        with patch("api.middleware.csrf.csrf_token_manager", manager):
            mock_request = MagicMock()
            mock_request.method = "POST"
            mock_request.headers = {"X-CSRF-Token": valid_token}
            mock_request.cookies = {"csrf_token": valid_token}
            await csrf_protect(mock_request)