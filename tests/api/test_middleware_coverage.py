"""
Additional Middleware Tests for Coverage

Tests for uncovered code paths in middleware modules.
"""

import time
from unittest.mock import MagicMock, patch

import pytest
from api.middleware.csrf import (
    CSRF_TOKEN_COOKIE_NAME,
    CSRFMiddleware,
    CSRFTokenManager,
)
from api.middleware.rate_limit import (
    InMemoryRateLimiter,
    RateLimitConfig,
    SlidingWindowEntry,
    get_client_identifier,
    rate_limit,
)
from api.middleware.security_headers import (
    SecurityHeadersConfig,
    SecurityHeadersMiddleware,
)
from fastapi import HTTPException, Request


class TestCSRFTokenManagerUncovered:
    """Tests for uncovered CSRFTokenManager code paths."""

    def test_generate_token_with_custom_secret(self):
        """Test generate_token with custom secret key."""
        manager = CSRFTokenManager(secret_key="custom_secret_key_12345")
        token = manager.generate_token()
        assert isinstance(token, str)
        assert len(token) > 0
        parts = token.split(".")
        assert len(parts) == 3

    def test_generate_token_default_secret(self):
        """Test generate_token uses default secret when none provided."""
        manager = CSRFTokenManager()
        token = manager.generate_token()
        assert isinstance(token, str)

    def test_sign_token_produces_consistent_signature(self):
        """Test _sign_token produces consistent results."""
        manager = CSRFTokenManager(secret_key="test_secret")
        token = "abc123"
        timestamp = 1234567890
        sig1 = manager._sign_token(token, timestamp)
        sig2 = manager._sign_token(token, timestamp)
        assert sig1 == sig2
        assert len(sig1) == 16

    def test_validate_token_with_future_timestamp(self):
        """Test validate_token accepts future timestamps (clock skew tolerance)."""
        manager = CSRFTokenManager()
        token = manager.generate_token()
        assert manager.validate_token(token) is True

    def test_validate_token_with_recent_timestamp(self):
        """Test validate_token with recent timestamp."""
        manager = CSRFTokenManager()
        token = manager.generate_token()
        assert manager.validate_token(token) is True

    def test_extract_token_from_header_x_csrf_token(self):
        """Test extracting token from X-CSRF-Token header."""
        manager = CSRFTokenManager()
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"X-CSRF-Token": "test_token_value"}
        token = manager.extract_token_from_header(mock_request)
        assert token == "test_token_value"

    def test_extract_token_from_header_lowercase(self):
        """Test extracting token from lowercase header."""
        manager = CSRFTokenManager()
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"x-csrf-token": "lowercase_token"}
        token = manager.extract_token_from_header(mock_request)
        assert token == "lowercase_token"

    def test_extract_token_from_header_not_found(self):
        """Test extract_token returns None when header missing."""
        manager = CSRFTokenManager()
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {}
        token = manager.extract_token_from_header(mock_request)
        assert token is None

    def test_extract_token_from_cookie(self):
        """Test extracting token from cookies."""
        manager = CSRFTokenManager()
        mock_request = MagicMock(spec=Request)
        mock_request.cookies = {CSRF_TOKEN_COOKIE_NAME: "cookie_token"}
        token = manager.extract_token_from_cookie(mock_request)
        assert token == "cookie_token"

    def test_extract_token_from_cookie_not_found(self):
        """Test extract_token_from_cookie returns None when cookie missing."""
        manager = CSRFTokenManager()
        mock_request = MagicMock(spec=Request)
        mock_request.cookies = {}
        token = manager.extract_token_from_cookie(mock_request)
        assert token is None


class TestCSRFMiddlewareUncovered:
    """Tests for uncovered CSRFMiddleware code paths."""

    def test_is_path_safe_with_exclude_paths(self):
        """Test _is_path_safe with exclude_paths."""
        middleware = CSRFMiddleware(
            app=MagicMock(),
            exclude_paths=["/api/admin/"]
        )
        assert middleware._is_path_safe("/api/admin/users") is True
        assert middleware._is_path_safe("/api/users") is False

    def test_is_path_safe_empty_lists(self):
        """Test _is_path_safe with empty safe_paths and exclude_paths."""
        middleware = CSRFMiddleware(
            app=MagicMock(),
            safe_paths=[],
            exclude_paths=[]
        )
        assert middleware._is_path_safe("/any/path") is False

    def test_is_state_changing_get(self):
        """Test _is_state_changing returns False for GET."""
        middleware = CSRFMiddleware(app=MagicMock())
        assert middleware._is_state_changing("GET") is False
        assert middleware._is_state_changing("HEAD") is False
        assert middleware._is_state_changing("OPTIONS") is False

    def test_is_state_changing_post(self):
        """Test _is_state_changing returns True for POST."""
        middleware = CSRFMiddleware(app=MagicMock())
        assert middleware._is_state_changing("POST") is True
        assert middleware._is_state_changing("PUT") is True
        assert middleware._is_state_changing("PATCH") is True
        assert middleware._is_state_changing("DELETE") is True

    @pytest.mark.asyncio
    async def test_dispatch_safe_path_skips_csrf(self):
        """Test dispatch skips CSRF check for safe paths."""
        middleware = CSRFMiddleware(app=MagicMock())

        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/api/monitor/health"
        mock_request.method = "POST"

        async def mock_call_next(req):
            return MagicMock()

        response = await middleware.dispatch(mock_request, mock_call_next)
        assert response is not None

    @pytest.mark.asyncio
    async def test_dispatch_safe_method_skips_csrf(self):
        """Test dispatch skips CSRF check for safe methods."""
        middleware = CSRFMiddleware(app=MagicMock())

        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/api/chapters"
        mock_request.method = "GET"

        async def mock_call_next(req):
            return MagicMock()

        response = await middleware.dispatch(mock_request, mock_call_next)
        assert response is not None


class TestRateLimiterUncovered:
    """Tests for uncovered rate limiter code paths."""

    def test_sliding_window_entry_default(self):
        """Test SlidingWindowEntry with default timestamps."""
        entry = SlidingWindowEntry()
        assert entry.timestamps == []

    def test_sliding_window_entry_with_values(self):
        """Test SlidingWindowEntry with specific timestamps."""
        now = time.time()
        entry = SlidingWindowEntry(timestamps=[now])
        assert entry.timestamps == [now]

    def test_rate_limit_config_with_prefix(self):
        """Test RateLimitConfig with custom prefix."""
        config = RateLimitConfig(requests=50, window_seconds=120, key_prefix="custom_prefix")
        assert config.requests == 50
        assert config.window_seconds == 120
        assert config.key_prefix == "custom_prefix"

    @pytest.mark.asyncio
    async def test_in_memory_rate_limiter_key_separation(self):
        """Test rate limiter maintains separate counters per key."""
        limiter = InMemoryRateLimiter()

        result1 = await limiter.check_rate_limit("key1", max_requests=2, window_seconds=60)
        assert result1[0] is True

        result2 = await limiter.check_rate_limit("key2", max_requests=2, window_seconds=60)
        assert result2[0] is True

        result1_second = await limiter.check_rate_limit("key1", max_requests=2, window_seconds=60)
        assert result1_second[0] is True

        result1_third = await limiter.check_rate_limit("key1", max_requests=2, window_seconds=60)
        assert result1_third[0] is False

    def test_get_client_identifier_forwarded_for(self):
        """Test get_client_identifier with X-Forwarded-For header."""
        from api.middleware.rate_limit import rate_limit_settings
        original = rate_limit_settings.trust_x_forwarded_for
        rate_limit_settings.trust_x_forwarded_for = True
        try:
            mock_request = MagicMock(spec=Request)
            mock_request.headers = {
                "X-Forwarded-For": "192.168.1.1",
            }
            mock_request.client = MagicMock()
            mock_request.client.host = "localhost"

            identifier = get_client_identifier(mock_request)
            assert "192.168.1.1" in identifier
        finally:
            rate_limit_settings.trust_x_forwarded_for = original

    def test_get_client_identifier_real_ip(self):
        """Test get_client_identifier with X-Real-IP header."""
        from api.middleware.rate_limit import rate_limit_settings
        original = rate_limit_settings.trust_x_real_ip
        rate_limit_settings.trust_x_real_ip = True
        try:
            mock_request = MagicMock(spec=Request)
            mock_request.headers = {"X-Real-IP": "10.0.0.1"}
            mock_request.client = MagicMock()
            mock_request.client.host = "localhost"

            identifier = get_client_identifier(mock_request)
            assert "10.0.0.1" in identifier
        finally:
            rate_limit_settings.trust_x_real_ip = original


class TestSecurityHeadersUncovered:
    """Tests for uncovered security headers code paths."""

    def test_security_headers_config_hsts_preload(self):
        """Test SecurityHeadersConfig with HSTS preload flag."""
        config = SecurityHeadersConfig(
            hsts_include_subdomains=True,
            hsts_preload=True
        )
        header = config.get_hsts_header()
        assert "preload" in header

    def test_security_headers_config_custom_csp(self):
        """Test SecurityHeadersConfig with custom CSP values."""
        config = SecurityHeadersConfig(
            csp_default_src="'self'",
            csp_script_src="'self' 'unsafe-inline' 'nonce-random123'"
        )
        header = config.get_csp_header()
        assert "default-src 'self'" in header
        assert "script-src" in header

    @pytest.mark.asyncio
    async def test_security_headers_middleware_exclude_paths(self):
        """Test SecurityHeadersMiddleware excludes paths correctly."""
        config = SecurityHeadersConfig()
        middleware = SecurityHeadersMiddleware(
            app=MagicMock(),
            config=config,
            exclude_paths=["/api/monitor/health"]
        )

        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/api/monitor/health"

        async def mock_call_next(req):
            response = MagicMock()
            response.headers = {}
            return response

        response = await middleware.dispatch(mock_request, mock_call_next)
        assert "Strict-Transport-Security" not in response.headers

    @pytest.mark.asyncio
    async def test_security_headers_added_to_response(self):
        """Test security headers are actually added to response."""
        config = SecurityHeadersConfig()
        middleware = SecurityHeadersMiddleware(app=MagicMock(), config=config)

        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/api/chapters"

        async def mock_call_next(req):
            response = MagicMock()
            response.headers = {}
            return response

        response = await middleware.dispatch(mock_request, mock_call_next)
        assert "Strict-Transport-Security" in response.headers


class TestRateLimitDependency:
    """Tests for rate_limit dependency function."""

    @pytest.mark.asyncio
    async def test_rate_limit_dependency_allows_request(self):
        """Test rate_limit dependency allows request within limit."""
        config = RateLimitConfig(requests=100, window_seconds=60)

        async def mock_check_rate_limit(*args, **kwargs):
            return (True, 100, 0)

        with patch("api.middleware.rate_limit.rate_limiter") as mock_limiter:
            mock_limiter.check_rate_limit = mock_check_rate_limit

            mock_request = MagicMock(spec=Request)
            mock_request.url.path = "/api/test"

            result = await rate_limit(config)(mock_request)
            assert result is None

    @pytest.mark.asyncio
    async def test_rate_limit_dependency_blocks_request(self):
        """Test rate_limit dependency blocks request when limit exceeded."""
        config = RateLimitConfig(requests=100, window_seconds=60)

        async def mock_check_rate_limit(*args, **kwargs):
            return (False, 0, 60)

        with patch("api.middleware.rate_limit.rate_limiter") as mock_limiter:
            mock_limiter.check_rate_limit = mock_check_rate_limit

            mock_request = MagicMock(spec=Request)
            mock_request.url.path = "/api/test"

            with pytest.raises(HTTPException) as exc_info:
                await rate_limit(config)(mock_request)

            assert exc_info.value.status_code == 429
