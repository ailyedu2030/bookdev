"""
Rate Limit Middleware Tests

Tests for rate limiting middleware and in-memory rate limiter.
"""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from api.middleware.rate_limit import (
    DEFAULT_RATE_LIMITS,
    InMemoryRateLimiter,
    RateLimitConfig,
    RateLimitMiddleware,
    SlidingWindowEntry,
    get_client_identifier,
    rate_limit,
)


class TestInMemoryRateLimiter:
    """Tests for InMemoryRateLimiter class"""

    @pytest.mark.asyncio
    async def test_check_rate_limit_first_request(self):
        """Test first request is allowed"""
        limiter = InMemoryRateLimiter()
        allowed, remaining, reset = await limiter.check_rate_limit("key1", 10, 60)
        assert allowed is True
        assert remaining == 9

    @pytest.mark.asyncio
    async def test_check_rate_limit_multiple_requests(self):
        """Test multiple requests within limit"""
        limiter = InMemoryRateLimiter()
        last_remaining = 0
        for _i in range(5):
            allowed, last_remaining, _ = await limiter.check_rate_limit("key2", 10, 60)
            assert allowed is True
        assert last_remaining == 5

    @pytest.mark.asyncio
    async def test_check_rate_limit_exceeds_limit(self):
        """Test requests exceeding limit are blocked"""
        limiter = InMemoryRateLimiter()
        for _i in range(10):
            await limiter.check_rate_limit("key3", 10, 60)
        allowed, remaining, reset = await limiter.check_rate_limit("key3", 10, 60)
        assert allowed is False
        assert remaining == 0

    @pytest.mark.asyncio
    async def test_check_rate_limit_different_keys_independent(self):
        """Test different keys have independent limits"""
        limiter = InMemoryRateLimiter()
        await limiter.check_rate_limit("keyA", 5, 60)
        await limiter.check_rate_limit("keyA", 5, 60)
        await limiter.check_rate_limit("keyA", 5, 60)
        allowed, remaining, _ = await limiter.check_rate_limit("keyB", 10, 60)
        assert allowed is True
        assert remaining == 9

    @pytest.mark.asyncio
    async def test_check_rate_limit_window_expiry(self):
        """Test window expiry allows new requests"""
        limiter = InMemoryRateLimiter()
        current_time = time.time()
        entry = SlidingWindowEntry(timestamps=[current_time - 120])
        limiter._storage["old_key"] = entry
        allowed, remaining, _ = await limiter.check_rate_limit("old_key", 10, 60)
        assert allowed is True

    def test_cleanup_skips_when_interval_not_elapsed(self):
        """Test cleanup skips when interval hasn't elapsed"""
        limiter = InMemoryRateLimiter()
        current_time = time.time()
        limiter._last_cleanup = current_time - 1800
        limiter._cleanup_expired(current_time)
        assert limiter._last_cleanup == current_time - 1800

    def test_cleanup_keeps_recent_entries(self):
        """Test cleanup keeps entries within window"""
        limiter = InMemoryRateLimiter()
        current_time = time.time()
        limiter._storage["recent"] = SlidingWindowEntry(timestamps=[current_time - 30])
        limiter._last_cleanup = current_time - 3600
        limiter._cleanup_expired(current_time)
        assert "recent" in limiter._storage


class TestSlidingWindowEntry:
    """Tests for SlidingWindowEntry dataclass"""

    def test_default_timestamps_is_empty_list(self):
        """Test default timestamps is empty list"""
        entry = SlidingWindowEntry()
        assert entry.timestamps == []

    def test_timestamps_can_be_modified(self):
        """Test timestamps can be added"""
        entry = SlidingWindowEntry()
        entry.timestamps.append(time.time())
        assert len(entry.timestamps) == 1


class TestRateLimitConfig:
    """Tests for RateLimitConfig dataclass"""

    def test_default_key_prefix(self):
        """Test default key prefix"""
        config = RateLimitConfig(requests=100, window_seconds=60)
        assert config.key_prefix == "rl"

    def test_custom_key_prefix(self):
        """Test custom key prefix"""
        config = RateLimitConfig(requests=100, window_seconds=60, key_prefix="custom")
        assert config.key_prefix == "custom"


class TestGetClientIdentifier:
    """Tests for get_client_identifier function"""

    def test_x_forwarded_for_header(self):
        """Test extraction from X-Forwarded-For header when trust is enabled"""
        from api.middleware.rate_limit import rate_limit_settings
        original = rate_limit_settings.trust_x_forwarded_for
        rate_limit_settings.trust_x_forwarded_for = True
        try:
            mock_request = MagicMock()
            mock_request.headers = {"X-Forwarded-For": "192.168.1.1, 10.0.0.1"}
            mock_request.client = None
            assert get_client_identifier(mock_request) == "192.168.1.1"
        finally:
            rate_limit_settings.trust_x_forwarded_for = original

    def test_x_real_ip_header(self):
        """Test extraction from X-Real-IP header when trust is enabled"""
        from api.middleware.rate_limit import rate_limit_settings
        original = rate_limit_settings.trust_x_real_ip
        rate_limit_settings.trust_x_real_ip = True
        try:
            mock_request = MagicMock()
            mock_request.headers = {"X-Real-IP": "192.168.1.2"}
            mock_request.client = None
            assert get_client_identifier(mock_request) == "192.168.1.2"
        finally:
            rate_limit_settings.trust_x_real_ip = original

    def test_client_host_fallback(self):
        """Test fallback to client host"""
        mock_request = MagicMock()
        mock_request.headers = {}
        mock_request.client.host = "127.0.0.1"
        assert get_client_identifier(mock_request) == "127.0.0.1"

    def test_unknown_when_no_source(self):
        """Test returns unknown when no source available"""
        mock_request = MagicMock()
        mock_request.headers = {}
        mock_request.client = None
        assert get_client_identifier(mock_request) == "unknown"


class TestRateLimitDependency:
    """Tests for rate_limit dependency"""

    @pytest.mark.asyncio
    async def test_rate_limit_allows_within_limit(self):
        """Test rate limit allows requests within limit"""
        limiter = InMemoryRateLimiter()
        config = RateLimitConfig(requests=10, window_seconds=60, key_prefix="test")
        with patch("api.middleware.rate_limit.rate_limiter", limiter):
            dep = rate_limit(config=config)
            mock_request = MagicMock()
            mock_request.headers = {"X-Forwarded-For": "192.168.1.100"}
            await dep(mock_request)




class TestRateLimitMiddleware:
    """Tests for RateLimitMiddleware class"""

    @pytest.mark.asyncio
    async def test_dispatch_exempt_path_bypasses(self):
        """Test exempt path bypasses rate limiting"""
        middleware = RateLimitMiddleware(app=MagicMock())
        mock_request = MagicMock()
        mock_request.url.path = "/api/monitor/health"
        mock_response = MagicMock()
        mock_response.status_code = 200
        call_next = AsyncMock(return_value=mock_response)
        await middleware.dispatch(mock_request, call_next)
        call_next.assert_called_once()

    @pytest.mark.asyncio
    async def test_dispatch_sets_rate_limit_headers(self):
        """Test response includes rate limit headers"""
        limiter = InMemoryRateLimiter()
        with patch("api.middleware.rate_limit.rate_limiter", limiter):
            middleware = RateLimitMiddleware(app=MagicMock())
            mock_request = MagicMock()
            mock_request.url.path = "/api/users"
            mock_request.headers = {"X-Forwarded-For": "192.168.1.50"}
            mock_request.client = MagicMock()
            mock_request.client.host = "192.168.1.50"
            mock_response = MagicMock()
            mock_response.headers = {}
            call_next = AsyncMock(return_value=mock_response)
            await middleware.dispatch(mock_request, call_next)
            assert "X-RateLimit-Limit" in mock_response.headers
            assert "X-RateLimit-Remaining" in mock_response.headers

    @pytest.mark.asyncio
    async def test_dispatch_returns_429_when_rate_limited(self):
        """Test rate limited response returns 429 status"""
        from starlette.responses import JSONResponse
        limiter = InMemoryRateLimiter()
        limiter._storage["anon:blocked"] = SlidingWindowEntry(timestamps=[time.time() - 10] * 30)
        with patch("api.middleware.rate_limit.rate_limiter", limiter):
            middleware = RateLimitMiddleware(app=MagicMock())
            mock_request = MagicMock()
            mock_request.url.path = "/api/test"
            mock_request.headers = {}
            mock_request.client.host = "blocked"
            response = await middleware.dispatch(mock_request, AsyncMock())
            assert isinstance(response, JSONResponse)
            assert response.status_code == 429

    def test_custom_exempt_paths(self):
        """Test custom exempt paths configuration"""
        middleware = RateLimitMiddleware(
            app=MagicMock(),
            exempt_paths=["/custom/exempt"],
        )
        assert middleware.exempt_paths == ["/custom/exempt"]


class TestDefaultRateLimits:
    """Tests for DEFAULT_RATE_LIMITS configuration"""

    def test_default_limits_exist(self):
        """Test all default rate limits are defined"""
        assert "anonymous" in DEFAULT_RATE_LIMITS
        assert "authenticated" in DEFAULT_RATE_LIMITS
        assert "strict" in DEFAULT_RATE_LIMITS
        assert "auth_login" in DEFAULT_RATE_LIMITS
        assert "auth_register" in DEFAULT_RATE_LIMITS

    def test_anonymous_rate_limit(self):
        """Test anonymous rate limit values"""
        config = DEFAULT_RATE_LIMITS["anonymous"]
        assert config.requests == 30
        assert config.window_seconds == 60

    def test_authenticated_rate_limit(self):
        """Test authenticated rate limit values"""
        config = DEFAULT_RATE_LIMITS["authenticated"]
        assert config.requests == 300
        assert config.window_seconds == 60

    def test_strict_rate_limit(self):
        """Test strict rate limit values"""
        config = DEFAULT_RATE_LIMITS["strict"]
        assert config.requests == 10
        assert config.window_seconds == 60

    def test_auth_login_rate_limit(self):
        """Test auth login rate limit values"""
        config = DEFAULT_RATE_LIMITS["auth_login"]
        assert config.requests == 5
        assert config.window_seconds == 60

    def test_auth_register_rate_limit(self):
        """Test auth register rate limit values"""
        config = DEFAULT_RATE_LIMITS["auth_register"]
        assert config.requests == 3
        assert config.window_seconds == 3600
