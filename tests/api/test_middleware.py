"""
Unit Tests for API Middleware Components

Tests for:
- CSRF Token Manager
- CSRF Middleware
- Rate Limiting
- Security Headers
"""

import asyncio
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi import Request, HTTPException
from fastapi.testclient import TestClient
from fastapi import FastAPI
from starlette.responses import Response

from api.middleware.csrf import (
    CSRFTokenManager,
    CSRFMiddleware,
    csrf_protect,
    csrf_token_manager,
    CSRF_TOKEN_COOKIE_NAME,
    CSRF_TOKEN_HEADER_NAME,
    SAFE_METHODS,
)
from api.middleware.rate_limit import (
    InMemoryRateLimiter,
    RateLimitConfig,
    RateLimitMiddleware,
    SlidingWindowEntry,
    rate_limit,
    get_client_identifier,
    rate_limit_settings,
)
from api.middleware.security_headers import (
    SecurityHeadersConfig,
    SecurityHeadersMiddleware,
    DEFAULT_SECURITY_CONFIG,
)


class TestCSRFTokenManager:
    """Tests for CSRFTokenManager"""

    def test_generate_token_returns_string(self):
        """Test that generate_token returns a token string"""
        manager = CSRFTokenManager()
        token = manager.generate_token()

        assert isinstance(token, str)
        assert len(token) > 0

    def test_generate_token_format(self):
        """Test that token has correct format (value.timestamp.signature)"""
        manager = CSRFTokenManager()
        token = manager.generate_token()

        parts = token.split(".")
        assert len(parts) == 3

    def test_generate_token_unique(self):
        """Test that each token is unique"""
        manager = CSRFTokenManager()
        token1 = manager.generate_token()
        time.sleep(0.01)
        token2 = manager.generate_token()

        assert token1 != token2

    def test_validate_token_valid(self):
        """Test validating a valid token"""
        manager = CSRFTokenManager()
        token = manager.generate_token()

        result = manager.validate_token(token)

        assert result is True

    def test_validate_token_empty(self):
        """Test validating empty token"""
        manager = CSRFTokenManager()

        result = manager.validate_token("")

        assert result is False

    def test_validate_token_invalid_format(self):
        """Test validating token with invalid format"""
        manager = CSRFTokenManager()

        result = manager.validate_token("invalid-token")

        assert result is False

    def test_validate_token_wrong_parts_count(self):
        """Test validating token with wrong number of parts"""
        manager = CSRFTokenManager()

        result = manager.validate_token("a.b")

        assert result is False

    def test_validate_token_invalid_signature(self):
        """Test validating token with wrong signature"""
        manager = CSRFTokenManager()
        token = manager.generate_token()
        parts = token.split(".")
        parts[2] = "0000000000000000"
        tampered_token = ".".join(parts)

        result = manager.validate_token(tampered_token)

        assert result is False

    def test_validate_token_expired(self):
        """Test validating expired token"""
        manager = CSRFTokenManager(secret_key="test-secret")
        old_timestamp = int(time.time()) - 7200
        token_value = "a" * 64
        signature = manager._sign_token(token_value, old_timestamp)
        expired_token = f"{token_value}.{old_timestamp}.{signature}"

        result = manager.validate_token(expired_token)

        assert result is False

    def test_extract_token_from_header(self):
        """Test extracting token from header"""
        manager = CSRFTokenManager()
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {
            CSRF_TOKEN_HEADER_NAME: "test-token",
            "x-csrf-token": "different-token",
        }

        result = manager.extract_token_from_header(mock_request)

        assert result == "test-token"

    def test_extract_token_from_header_lowercase(self):
        """Test extracting token from header with lowercase key"""
        manager = CSRFTokenManager()
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {
            "x-csrf-token": "test-token",
        }

        result = manager.extract_token_from_header(mock_request)

        assert result == "test-token"

    def test_extract_token_from_header_not_found(self):
        """Test extracting token when not in header"""
        manager = CSRFTokenManager()
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {}

        result = manager.extract_token_from_header(mock_request)

        assert result is None

    def test_extract_token_from_cookie(self):
        """Test extracting token from cookie"""
        manager = CSRFTokenManager()
        mock_request = MagicMock(spec=Request)
        mock_request.cookies = {
            CSRF_TOKEN_COOKIE_NAME: "cookie-token",
        }

        result = manager.extract_token_from_cookie(mock_request)

        assert result == "cookie-token"

    def test_extract_token_from_cookie_not_found(self):
        """Test extracting token when not in cookies"""
        manager = CSRFTokenManager()
        mock_request = MagicMock(spec=Request)
        mock_request.cookies = {}

        result = manager.extract_token_from_cookie(mock_request)

        assert result is None


class TestSafeMethods:
    """Tests for SAFE_METHODS constant"""

    def test_safe_methods_contains_get(self):
        """Test that GET is a safe method"""
        assert "GET" in SAFE_METHODS

    def test_safe_methods_contains_head(self):
        """Test that HEAD is a safe method"""
        assert "HEAD" in SAFE_METHODS

    def test_safe_methods_contains_options(self):
        """Test that OPTIONS is a safe method"""
        assert "OPTIONS" in SAFE_METHODS

    def test_safe_methods_does_not_contain_post(self):
        """Test that POST is not a safe method"""
        assert "POST" not in SAFE_METHODS

    def test_safe_methods_does_not_contain_put(self):
        """Test that PUT is not a safe method"""
        assert "PUT" not in SAFE_METHODS

    def test_safe_methods_does_not_contain_delete(self):
        """Test that DELETE is not a safe method"""
        assert "DELETE" not in SAFE_METHODS


class TestCSRFMiddleware:
    """Tests for CSRFMiddleware"""

    def test_is_path_safe_with_safe_paths(self):
        """Test _is_path_safe with configured safe paths"""
        middleware = CSRFMiddleware(
            app=MagicMock(),
            safe_paths=["/api/public", "/docs"],
        )

        assert middleware._is_path_safe("/api/public/data") is True
        assert middleware._is_path_safe("/docs") is True
        assert middleware._is_path_safe("/api/private") is False

    def test_is_path_safe_with_exclude_paths(self):
        """Test _is_path_safe with exclude paths"""
        middleware = CSRFMiddleware(
            app=MagicMock(),
            exclude_paths=["/api/admin"],
        )

        assert middleware._is_path_safe("/api/admin/users") is True
        assert middleware._is_path_safe("/api/public") is False

    def test_is_state_changing_safe_method(self):
        """Test _is_state_changing with safe methods"""
        middleware = CSRFMiddleware(app=MagicMock())

        assert middleware._is_state_changing("GET") is False
        assert middleware._is_state_changing("HEAD") is False
        assert middleware._is_state_changing("OPTIONS") is False

    def test_is_state_changing_unsafe_method(self):
        """Test _is_state_changing with unsafe methods"""
        middleware = CSRFMiddleware(app=MagicMock())

        assert middleware._is_state_changing("POST") is True
        assert middleware._is_state_changing("PUT") is True
        assert middleware._is_state_changing("PATCH") is True
        assert middleware._is_state_changing("DELETE") is True


class TestInMemoryRateLimiter:
    """Tests for InMemoryRateLimiter"""

    @pytest.mark.asyncio
    async def test_check_rate_limit_first_request(self):
        """Test first request is allowed"""
        limiter = InMemoryRateLimiter()

        allowed, remaining, reset = await limiter.check_rate_limit("test-key", 10, 60)

        assert allowed is True
        assert remaining == 9

    @pytest.mark.asyncio
    async def test_check_rate_limit_within_limit(self):
        """Test requests within limit are allowed"""
        limiter = InMemoryRateLimiter()

        for i in range(5):
            allowed, remaining, _ = await limiter.check_rate_limit("test-key", 10, 60)
            assert allowed is True
            assert remaining == 9 - i

    @pytest.mark.asyncio
    async def test_check_rate_limit_exceeded(self):
        """Test requests exceeding limit are blocked"""
        limiter = InMemoryRateLimiter()

        for i in range(10):
            await limiter.check_rate_limit("test-key", 10, 60)

        allowed, remaining, reset = await limiter.check_rate_limit("test-key", 10, 60)

        assert allowed is False
        assert remaining == 0

    @pytest.mark.asyncio
    async def test_check_rate_limit_different_keys(self):
        """Test that different keys have separate limits"""
        limiter = InMemoryRateLimiter()

        for i in range(10):
            await limiter.check_rate_limit("key1", 10, 60)

        allowed, remaining, _ = await limiter.check_rate_limit("key2", 10, 60)

        assert allowed is True
        assert remaining == 9

    @pytest.mark.asyncio
    async def test_check_rate_limit_window_expires(self):
        """Test that rate limit resets after window"""
        limiter = InMemoryRateLimiter()

        for i in range(10):
            await limiter.check_rate_limit("test-key", 10, 1)
            await asyncio.sleep(0.1)

        allowed, remaining, _ = await limiter.check_rate_limit("test-key", 10, 1)

        assert allowed is True


class TestRateLimitConfig:
    """Tests for RateLimitConfig"""

    def test_rate_limit_config_defaults(self):
        """Test RateLimitConfig with defaults"""
        config = RateLimitConfig(requests=100, window_seconds=60)

        assert config.requests == 100
        assert config.window_seconds == 60
        assert config.key_prefix == "rl"

    def test_rate_limit_config_custom_prefix(self):
        """Test RateLimitConfig with custom prefix"""
        config = RateLimitConfig(requests=50, window_seconds=30, key_prefix="custom")

        assert config.key_prefix == "custom"


class TestSlidingWindowEntry:
    """Tests for SlidingWindowEntry"""

    def test_sliding_window_entry_defaults(self):
        """Test SlidingWindowEntry default values"""
        entry = SlidingWindowEntry()

        assert entry.timestamps == []

    def test_sliding_window_entry_with_timestamps(self):
        """Test SlidingWindowEntry with initial timestamps"""
        entry = SlidingWindowEntry(timestamps=[1.0, 2.0, 3.0])

        assert len(entry.timestamps) == 3


class TestGetClientIdentifier:
    """Tests for get_client_identifier"""

    def test_get_client_identifier_x_forwarded_for(self):
        """Test getting client ID from X-Forwarded-For header"""
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"X-Forwarded-For": "192.168.1.1, 10.0.0.1"}
        mock_request.client = MagicMock(host="127.0.0.1")

        original = rate_limit_settings.trust_x_forwarded_for
        rate_limit_settings.trust_x_forwarded_for = True
        try:
            result = get_client_identifier(mock_request)
            assert result == "192.168.1.1"
        finally:
            rate_limit_settings.trust_x_forwarded_for = original

    def test_get_client_identifier_x_real_ip(self):
        """Test getting client ID from X-Real-IP header"""
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"X-Real-IP": "192.168.1.100"}
        mock_request.client = MagicMock(host="127.0.0.1")

        original = rate_limit_settings.trust_x_real_ip
        rate_limit_settings.trust_x_real_ip = True
        try:
            result = get_client_identifier(mock_request)
            assert result == "192.168.1.100"
        finally:
            rate_limit_settings.trust_x_real_ip = original

    def test_get_client_identifier_client_host(self):
        """Test getting client ID from client host"""
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {}
        mock_request.client = MagicMock(host="192.168.1.50")

        result = get_client_identifier(mock_request)

        assert result == "192.168.1.50"

    def test_get_client_identifier_unknown(self):
        """Test getting client ID when no client info available"""
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {}
        mock_request.client = None

        result = get_client_identifier(mock_request)

        assert result == "unknown"


class TestSecurityHeadersConfig:
    """Tests for SecurityHeadersConfig"""

    def test_security_headers_config_defaults(self):
        """Test SecurityHeadersConfig with defaults"""
        config = SecurityHeadersConfig()

        assert config.hsts_max_age == 31536000
        assert config.hsts_include_subdomains is True
        assert config.hsts_preload is True
        assert config.x_frame_options == "DENY"
        assert config.x_content_type_options == "nosniff"

    def test_get_hsts_header_basic(self):
        """Test getting basic HSTS header"""
        config = SecurityHeadersConfig(
            hsts_max_age=31536000,
            hsts_include_subdomains=False,
            hsts_preload=False,
        )

        result = config.get_hsts_header()

        assert result == "max-age=31536000"

    def test_get_hsts_header_with_subdomains(self):
        """Test HSTS header with includeSubDomains"""
        config = SecurityHeadersConfig(
            hsts_max_age=31536000,
            hsts_include_subdomains=True,
            hsts_preload=False,
        )

        result = config.get_hsts_header()

        assert "max-age=31536000" in result
        assert "includeSubDomains" in result

    def test_get_hsts_header_with_preload(self):
        """Test HSTS header with preload"""
        config = SecurityHeadersConfig(
            hsts_max_age=31536000,
            hsts_include_subdomains=True,
            hsts_preload=True,
        )

        result = config.get_hsts_header()

        assert "max-age=31536000" in result
        assert "includeSubDomains" in result
        assert "preload" in result

    def test_get_csp_header(self):
        """Test getting CSP header"""
        config = SecurityHeadersConfig(
            csp_default_src="'self'",
            csp_script_src="'self'",
            csp_style_src="'self'",
            csp_img_src="'self' data:",
            csp_connect_src="'self' https://api.example.com",
            csp_frame_ancestors="'none'",
        )

        result = config.get_csp_header()

        assert "default-src 'self'" in result
        assert "script-src 'self'" in result
        assert "frame-ancestors 'none'" in result


class TestSecurityHeadersMiddleware:
    """Tests for SecurityHeadersMiddleware"""

    def test_security_headers_middleware_exclude_paths(self):
        """Test that exclude paths work"""
        middleware = SecurityHeadersMiddleware(
            app=MagicMock(),
            exclude_paths=["/api/public"],
        )

        assert middleware.exclude_paths == ["/api/public"]

    def test_security_headers_middleware_default_config(self):
        """Test middleware uses default config when not provided"""
        middleware = SecurityHeadersMiddleware(app=MagicMock())

        assert middleware.config == DEFAULT_SECURITY_CONFIG


class TestCSRFMiddlewareDispatch:
    """Tests for CSRFMiddleware dispatch method"""

    @pytest.mark.asyncio
    async def test_dispatch_safe_path_skips(self):
        """Test that safe paths skip CSRF check"""
        app = MagicMock()
        app.return_value = AsyncMock()
        middleware = CSRFMiddleware(app=app, safe_paths=["/api/public"])

        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/api/public/data"
        mock_request.method = "POST"

        async def call_next(req):
            return Response(content="OK")

        result = await middleware.dispatch(mock_request, call_next)
        assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_dispatch_safe_method_skips(self):
        """Test that safe methods skip CSRF check"""
        app = MagicMock()
        middleware = CSRFMiddleware(app=app)

        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/api/private"
        mock_request.method = "GET"

        async def call_next(req):
            return Response(content="OK")

        result = await middleware.dispatch(mock_request, call_next)
        assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_dispatch_post_without_token_returns_403(self):
        """Test POST without CSRF token returns 403"""
        middleware = CSRFMiddleware(app=MagicMock())

        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/api/private"
        mock_request.method = "POST"
        mock_request.headers = {}
        mock_request.cookies = {}

        async def call_next(req):
            return Response(content="OK")

        result = await middleware.dispatch(mock_request, call_next)
        assert result.status_code == 403

    @pytest.mark.asyncio
    async def test_dispatch_post_with_invalid_token_returns_403(self):
        """Test POST with invalid CSRF token returns 403"""
        middleware = CSRFMiddleware(app=MagicMock())

        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/api/private"
        mock_request.method = "POST"
        mock_request.headers = {"X-CSRF-Token": "invalid-token"}
        mock_request.cookies = {"csrf_token": "different-token"}

        async def call_next(req):
            return Response(content="OK")

        result = await middleware.dispatch(mock_request, call_next)
        assert result.status_code == 403

    @pytest.mark.asyncio
    async def test_dispatch_put_with_valid_tokens_passes(self):
        """Test that PUT with valid CSRF tokens passes"""
        app = MagicMock()
        token_manager = CSRFTokenManager()
        middleware = CSRFMiddleware(app=app, token_manager=token_manager)

        token = token_manager.generate_token()

        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/api/private"
        mock_request.method = "PUT"
        mock_request.headers = {"X-CSRF-Token": token}
        mock_request.cookies = {"csrf_token": token}

        mock_response = MagicMock()
        mock_response.headers = {}

        async def call_next(req):
            return mock_response

        result = await middleware.dispatch(mock_request, call_next)
        assert result is mock_response


class TestCSRFProtectDependency:
    """Tests for csrf_protect dependency"""

    def test_csrf_protect_safe_method_passes(self):
        """Test that safe methods pass CSRF check"""
        import asyncio

        mock_request = MagicMock(spec=Request)
        mock_request.method = "GET"

        async def run():
            await csrf_protect(mock_request)

        asyncio.run(run())

    def test_csrf_protect_missing_token_raises(self):
        """Test that missing token raises HTTPException"""
        mock_request = MagicMock(spec=Request)
        mock_request.method = "POST"
        mock_request.headers = {}
        mock_request.cookies = {}

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(csrf_protect(mock_request))

        assert exc_info.value.status_code == 403


class TestRateLimitMiddleware:
    """Tests for RateLimitMiddleware"""

    @pytest.mark.asyncio
    async def test_rate_limit_exempt_path_skips(self):
        """Test that exempt paths skip rate limiting"""
        app = MagicMock()
        middleware = RateLimitMiddleware(
            app=app,
            exempt_paths=["/api/monitor/health"],
        )

        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/api/monitor/health"
        mock_request.headers = {}
        mock_request.client = MagicMock(host="127.0.0.1")

        async def call_next(req):
            return Response(content="OK")

        result = await middleware.dispatch(mock_request, call_next)
        assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_rate_limit_includes_headers(self):
        """Test that rate limit headers are included in response"""
        app = MagicMock()
        middleware = RateLimitMiddleware(app=app)

        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/api/test"
        mock_request.headers = {}
        mock_request.client = MagicMock(host="192.168.1.1")

        mock_response = MagicMock(spec=Response)
        mock_response.headers = {}

        async def call_next(req):
            return mock_response

        result = await middleware.dispatch(mock_request, call_next)
        assert "X-RateLimit-Limit" in dict(result.headers)

    @pytest.mark.asyncio
    async def test_rate_limit_decrements_remaining(self):
        """Test that remaining count decrements for same IP"""
        from api.middleware.rate_limit import InMemoryRateLimiter

        limiter = InMemoryRateLimiter()
        limiter._storage.clear()

        allowed1, remaining1, _ = await limiter.check_rate_limit("test-ip", 10, 60)
        allowed2, remaining2, _ = await limiter.check_rate_limit("test-ip", 10, 60)

        assert allowed1 is True
        assert allowed2 is True
        assert remaining2 == remaining1 - 1


class TestRateLimitDependency:
    """Tests for rate_limit dependency"""

    @pytest.mark.asyncio
    async def test_rate_limit_allows_within_limit(self):
        """Test that requests within limit are allowed"""
        from api.middleware.rate_limit import rate_limit, RateLimitConfig

        config = RateLimitConfig(requests=100, window_seconds=60)
        limiter = rate_limit(config)

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"X-Forwarded-For": "192.168.1.100"}
        mock_request.client = MagicMock(host="127.0.0.1")

        await limiter(mock_request)

    @pytest.mark.asyncio
    async def test_rate_limit_blocks_when_exceeded(self):
        """Test that requests over limit raise HTTPException"""
        from api.middleware.rate_limit import rate_limit, RateLimitConfig, InMemoryRateLimiter

        InMemoryRateLimiter()._storage.clear()

        config = RateLimitConfig(requests=2, window_seconds=60)
        limiter = rate_limit(config)

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {}
        mock_request.client = MagicMock(host="192.168.1.200")

        await limiter(mock_request)
        await limiter(mock_request)

        with pytest.raises(HTTPException) as exc_info:
            await limiter(mock_request)

        assert exc_info.value.status_code == 429


class TestSecurityHeadersMiddlewareDispatch:
    """Tests for SecurityHeadersMiddleware dispatch"""

    @pytest.mark.asyncio
    async def test_security_headers_added_to_response(self):
        """Test that security headers are added to response"""
        app = MagicMock()
        middleware = SecurityHeadersMiddleware(app=app)

        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/api/test"

        mock_response = MagicMock(spec=Response)
        mock_response.headers = {}

        async def call_next(req):
            return mock_response

        result = await middleware.dispatch(mock_request, call_next)

        assert "Strict-Transport-Security" in dict(result.headers)
        assert "Content-Security-Policy" in dict(result.headers)
        assert "X-Frame-Options" in dict(result.headers)
        assert "X-Content-Type-Options" in dict(result.headers)

    @pytest.mark.asyncio
    async def test_security_headers_excluded_for_path(self):
        """Test that security headers are excluded for specific paths"""
        app = MagicMock()
        middleware = SecurityHeadersMiddleware(
            app=app,
            exclude_paths=["/api/public"],
        )

        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/api/public/data"

        async def call_next(req):
            return Response(content="OK")

        result = await middleware.dispatch(mock_request, call_next)
        assert "Strict-Transport-Security" not in dict(result.headers)


class TestCSRFTokenManagerEdgeCases:
    """Edge case tests for CSRFTokenManager"""

    def test_validate_token_recent_timestamp(self):
        """Test validating token with recent timestamp is accepted"""
        manager = CSRFTokenManager()
        token = manager.generate_token()

        result = manager.validate_token(token)
        assert result is True

    def test_sign_token_consistency(self):
        """Test that _sign_token is consistent"""
        manager = CSRFTokenManager()
        sig1 = manager._sign_token("test-token", 1234567890)
        sig2 = manager._sign_token("test-token", 1234567890)

        assert sig1 == sig2

    def test_sign_token_different_inputs(self):
        """Test that different inputs produce different signatures"""
        manager = CSRFTokenManager()
        sig1 = manager._sign_token("token1", 1234567890)
        sig2 = manager._sign_token("token2", 1234567890)

        assert sig1 != sig2


class TestCSRFTokenManagerValueError:
    """Tests for CSRFTokenManager exception handling in validate_token"""

    def test_validate_token_non_integer_timestamp_raises_value_error(self):
        """Test that non-integer timestamp raises ValueError"""
        manager = CSRFTokenManager()
        manager._token_cache = {}

        result = manager.validate_token("token.abc.signature")

        assert result is False

    def test_validate_token_empty_parts_raises_index_error(self):
        """Test that empty token parts raise IndexError"""
        manager = CSRFTokenManager()
        manager._token_cache = {}

        result = manager.validate_token("..")

        assert result is False

    def test_validate_token_missing_signature_parts(self):
        """Test validating token with missing signature parts"""
        manager = CSRFTokenManager()

        result = manager.validate_token("tokenvalue.12345.")

        assert result is False


class TestCSRFMiddlewareDispatchMismatch:
    """Tests for CSRFMiddleware dispatch with token mismatch"""

    @pytest.mark.asyncio
    async def test_dispatch_token_mismatch_returns_403(self):
        """Test POST with mismatched CSRF tokens returns 403"""
        token_manager = CSRFTokenManager()
        middleware = CSRFMiddleware(app=MagicMock(), token_manager=token_manager)

        valid_token = token_manager.generate_token()
        different_token = token_manager.generate_token()

        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/api/private"
        mock_request.method = "POST"
        mock_request.headers = {"X-CSRF-Token": valid_token}
        mock_request.cookies = {"csrf_token": different_token}

        async def call_next(req):
            return Response(content="OK")

        result = await middleware.dispatch(mock_request, call_next)
        assert result.status_code == 403


class TestCSRFProtectDependencyCoverage:
    """Additional tests for csrf_protect dependency coverage"""

    def test_csrf_protect_with_invalid_token_raises(self):
        """Test that invalid token raises HTTPException"""
        mock_request = MagicMock(spec=Request)
        mock_request.method = "POST"
        mock_request.headers = {"X-CSRF-Token": "invalid-token"}
        mock_request.cookies = {"csrf_token": "different-invalid-token"}

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(csrf_protect(mock_request))

        assert exc_info.value.status_code == 403

    def test_csrf_protect_with_mismatch_token_raises(self):
        """Test that mismatched tokens raise HTTPException"""
        token_manager = CSRFTokenManager()
        mock_request = MagicMock(spec=Request)
        mock_request.method = "PUT"
        mock_request.headers = {"X-CSRF-Token": "valid-looking-token"}
        mock_request.cookies = {"csrf_token": "different-token"}

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(csrf_protect(mock_request))

        assert exc_info.value.status_code == 403


class TestInMemoryRateLimiterCleanup:
    """Tests for InMemoryRateLimiter cleanup"""

    @pytest.mark.asyncio
    async def test_cleanup_removes_expired_entries(self):
        """Test that _cleanup_expired removes entries with old timestamps"""
        limiter = InMemoryRateLimiter()
        limiter._storage.clear()
        limiter._cleanup_interval = 1
        limiter._last_cleanup = 0

        await limiter.check_rate_limit("key1", 10, 60)
        await limiter.check_rate_limit("key2", 10, 60)

        limiter._last_cleanup = 0
        current_time = time.time() + 2

        limiter._cleanup_expired(current_time)

        assert limiter._last_cleanup == current_time

    @pytest.mark.asyncio
    async def test_cleanup_skips_when_interval_not_reached(self):
        """Test that cleanup is skipped when interval not reached"""
        limiter = InMemoryRateLimiter()
        limiter._storage.clear()
        limiter._cleanup_interval = 3600
        limiter._last_cleanup = time.time()

        old_last_cleanup = limiter._last_cleanup

        await limiter.check_rate_limit("key1", 10, 60)

        assert limiter._last_cleanup == old_last_cleanup

    @pytest.mark.asyncio
    async def test_check_rate_limit_triggers_cleanup(self):
        """Test that check_rate_limit triggers cleanup when needed"""
        limiter = InMemoryRateLimiter()
        limiter._storage.clear()
        limiter._cleanup_interval = 1
        limiter._last_cleanup = time.time() - 2

        await limiter.check_rate_limit("test-key", 10, 60)

        assert limiter._last_cleanup > time.time() - 2


class TestRateLimitDependencyDefaultConfig:
    """Tests for rate_limit dependency with default config"""

    @pytest.mark.asyncio
    async def test_rate_limit_dependency_default_behavior(self):
        """Test that rate_limit dependency works without explicit config"""
        from api.middleware.rate_limit import rate_limit, DEFAULT_RATE_LIMITS

        limiter = rate_limit()

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {}
        mock_request.client = MagicMock(host="192.168.1.50")

        await limiter(mock_request)


class TestRateLimitMiddlewareExhausted:
    """Tests for RateLimitMiddleware when rate limit is exhausted"""

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded_returns_429(self):
        """Test that requests over limit return 429"""
        from api.middleware.rate_limit import RateLimitMiddleware, InMemoryRateLimiter

        InMemoryRateLimiter()._storage.clear()

        middleware = RateLimitMiddleware(
            app=MagicMock(),
            config=RateLimitConfig(requests=1, window_seconds=60),
        )

        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/api/test"
        mock_request.headers = {}
        mock_request.client = MagicMock(host="192.168.1.99")

        async def call_next(req):
            return Response(content="OK")

        result1 = await middleware.dispatch(mock_request, call_next)
        assert result1.status_code == 200

        result2 = await middleware.dispatch(mock_request, call_next)
        assert result2.status_code == 429


class TestInMemoryRateLimiterCleanupEntries:
    """Tests for InMemoryRateLimiter cleanup of empty entries"""

    @pytest.mark.asyncio
    async def test_cleanup_removes_entries_with_no_timestamps(self):
        """Test that _cleanup_expired deletes keys with empty timestamps"""
        limiter = InMemoryRateLimiter()
        limiter._storage.clear()
        limiter._cleanup_interval = 1
        limiter._last_cleanup = 0

        current_time = time.time()

        limiter._storage["old-key"] = SlidingWindowEntry(timestamps=[current_time - 4000])
        limiter._storage["another-old"] = SlidingWindowEntry(timestamps=[current_time - 5000])

        limiter._cleanup_expired(current_time)

        assert "old-key" not in limiter._storage
        assert "another-old" not in limiter._storage


class TestCSRFProtectMismatch:
    """Tests for csrf_protect with token mismatch"""

    def test_csrf_protect_token_mismatch_raises(self):
        """Test that csrf_protect raises when cookie and header tokens mismatch"""
        mock_request = MagicMock(spec=Request)
        mock_request.method = "POST"
        mock_request.headers = {"X-CSRF-Token": "header-token-value"}
        mock_request.cookies = {"csrf_token": "cookie-token-value"}

        def fake_validate(token: str) -> bool:
            return True

        with patch.object(csrf_token_manager, "validate_token", side_effect=fake_validate):
            with pytest.raises(HTTPException) as exc_info:
                asyncio.run(csrf_protect(mock_request))

        assert exc_info.value.status_code == 403
