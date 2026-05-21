"""
Security Headers Middleware Tests

Tests for security headers middleware including CSP, HSTS, X-Frame-Options, etc.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from api.middleware.security_headers import (
    DEFAULT_SECURITY_CONFIG,
    SecurityHeadersConfig,
    SecurityHeadersMiddleware,
)


class TestSecurityHeadersConfig:
    """Tests for SecurityHeadersConfig class"""

    def test_default_values(self):
        """Test default configuration values"""
        config = SecurityHeadersConfig()
        assert config.hsts_max_age == 31536000
        assert config.hsts_include_subdomains is True
        assert config.hsts_preload is True
        assert config.x_frame_options == "DENY"
        assert config.x_content_type_options == "nosniff"

    def test_custom_hsts_max_age(self):
        """Test custom HSTS max age"""
        config = SecurityHeadersConfig(hsts_max_age=63072000)
        assert config.hsts_max_age == 63072000

    def test_custom_csp_values(self):
        """Test custom CSP values"""
        config = SecurityHeadersConfig(
            csp_default_src="'self'",
            csp_script_src="'self' 'unsafe-inline'",
            csp_style_src="'self' 'unsafe-inline'",
            csp_img_src="'self' data:",
        )
        assert config.csp_default_src == "'self'"
        assert config.csp_script_src == "'self' 'unsafe-inline'"

    def test_custom_x_frame_options(self):
        """Test custom X-Frame-Options"""
        config = SecurityHeadersConfig(x_frame_options="SAMEORIGIN")
        assert config.x_frame_options == "SAMEORIGIN"

    def test_get_hsts_header_basic(self):
        """Test HSTS header generation"""
        config = SecurityHeadersConfig(hsts_max_age=31536000)
        header = config.get_hsts_header()
        assert "max-age=31536000" in header

    def test_get_hsts_header_with_subdomains(self):
        """Test HSTS header includes subdomains directive"""
        config = SecurityHeadersConfig(hsts_include_subdomains=True)
        header = config.get_hsts_header()
        assert "includeSubDomains" in header

    def test_get_hsts_header_with_preload(self):
        """Test HSTS header includes preload directive"""
        config = SecurityHeadersConfig(hsts_preload=True)
        header = config.get_hsts_header()
        assert "preload" in header

    def test_get_hsts_header_no_subdomains(self):
        """Test HSTS header without subdomains"""
        config = SecurityHeadersConfig(hsts_include_subdomains=False)
        header = config.get_hsts_header()
        assert "includeSubDomains" not in header

    def test_get_csp_header_basic(self):
        """Test CSP header generation"""
        config = SecurityHeadersConfig()
        header = config.get_csp_header()
        assert "default-src" in header
        assert "script-src" in header
        assert "style-src" in header
        assert "img-src" in header
        assert "connect-src" in header
        assert "frame-ancestors" in header

    def test_get_csp_header_format(self):
        """Test CSP header format uses semicolons"""
        config = SecurityHeadersConfig()
        header = config.get_csp_header()
        assert "; " in header


class TestDefaultSecurityConfig:
    """Tests for DEFAULT_SECURITY_CONFIG"""

    def test_default_config_exists(self):
        """Test default config is defined"""
        assert DEFAULT_SECURITY_CONFIG is not None

    def test_default_config_has_reasonable_values(self):
        """Test default config has reasonable security values"""
        assert DEFAULT_SECURITY_CONFIG.x_frame_options == "DENY"
        assert DEFAULT_SECURITY_CONFIG.x_content_type_options == "nosniff"


class TestSecurityHeadersMiddleware:
    """Tests for SecurityHeadersMiddleware class"""

    def test_init_with_default_config(self):
        """Test middleware initializes with default config"""
        middleware = SecurityHeadersMiddleware(app=MagicMock())
        assert middleware.config == DEFAULT_SECURITY_CONFIG

    def test_init_with_custom_config(self):
        """Test middleware initializes with custom config"""
        custom_config = SecurityHeadersConfig(hsts_max_age=63072000)
        middleware = SecurityHeadersMiddleware(app=MagicMock(), config=custom_config)
        assert middleware.config.hsts_max_age == 63072000

    def test_init_with_exclude_paths(self):
        """Test middleware initializes with exclude paths"""
        middleware = SecurityHeadersMiddleware(
            app=MagicMock(),
            exclude_paths=["/health", "/metrics"],
        )
        assert middleware.exclude_paths == ["/health", "/metrics"]

    def test_default_exclude_paths_empty(self):
        """Test default exclude paths is empty list"""
        middleware = SecurityHeadersMiddleware(app=MagicMock())
        assert middleware.exclude_paths == []

    @pytest.mark.asyncio
    async def test_dispatch_adds_security_headers(self):
        """Test dispatch adds security headers to response"""
        middleware = SecurityHeadersMiddleware(app=MagicMock())
        mock_request = MagicMock()
        mock_request.url.path = "/test"
        mock_response = MagicMock()
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)
        await middleware.dispatch(mock_request, call_next)
        assert "Strict-Transport-Security" in mock_response.headers
        assert "X-Frame-Options" in mock_response.headers
        assert "Content-Security-Policy" in mock_response.headers

    @pytest.mark.asyncio
    async def test_dispatch_adds_cross_origin_headers(self):
        """Test dispatch adds cross-origin security headers"""
        middleware = SecurityHeadersMiddleware(app=MagicMock())
        mock_request = MagicMock()
        mock_request.url.path = "/test"
        mock_response = MagicMock()
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)
        await middleware.dispatch(mock_request, call_next)
        assert "Cross-Origin-Opener-Policy" in mock_response.headers
        assert "Cross-Origin-Resource-Policy" in mock_response.headers
        assert "Cross-Origin-Embedder-Policy" in mock_response.headers

    @pytest.mark.asyncio
    async def test_dispatch_excludes_path(self):
        """Test dispatch skips headers for excluded paths"""
        middleware = SecurityHeadersMiddleware(
            app=MagicMock(),
            exclude_paths=["/health"],
        )
        mock_request = MagicMock()
        mock_request.url.path = "/health"
        mock_response = MagicMock()
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)
        await middleware.dispatch(mock_request, call_next)
        call_next.assert_called_once()
        assert len(mock_response.headers) == 0

    @pytest.mark.asyncio
    async def test_dispatch_passes_request(self):
        """Test dispatch passes request to call_next"""
        middleware = SecurityHeadersMiddleware(app=MagicMock())
        mock_request = MagicMock()
        mock_request.url.path = "/test"
        mock_response = MagicMock()
        call_next = AsyncMock(return_value=mock_response)
        await middleware.dispatch(mock_request, call_next)
        call_next.assert_called_once_with(mock_request)

    @pytest.mark.asyncio
    async def test_dispatch_hsts_value_from_config(self):
        """Test HSTS header value comes from config"""
        custom_config = SecurityHeadersConfig(hsts_max_age=63072000, hsts_include_subdomains=False, hsts_preload=False)
        middleware = SecurityHeadersMiddleware(app=MagicMock(), config=custom_config)
        mock_request = MagicMock()
        mock_request.url.path = "/test"
        mock_response = MagicMock()
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)
        await middleware.dispatch(mock_request, call_next)
        assert mock_response.headers["Strict-Transport-Security"] == "max-age=63072000"

    @pytest.mark.asyncio
    async def test_dispatch_csp_value_from_config(self):
        """Test CSP header value comes from config"""
        custom_config = SecurityHeadersConfig(csp_default_src="'self'")
        middleware = SecurityHeadersMiddleware(app=MagicMock(), config=custom_config)
        mock_request = MagicMock()
        mock_request.url.path = "/test"
        mock_response = MagicMock()
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)
        await middleware.dispatch(mock_request, call_next)
        assert "default-src 'self'" in mock_response.headers["Content-Security-Policy"]


class TestSecurityHeadersEdgeCases:
    """Tests for edge cases in security headers"""

    @pytest.mark.asyncio
    async def test_multiple_excluded_paths(self):
        """Test multiple excluded paths work correctly"""
        middleware = SecurityHeadersMiddleware(
            app=MagicMock(),
            exclude_paths=["/health", "/metrics", "/status"],
        )
        mock_request = MagicMock()
        mock_request.url.path = "/metrics/prometheus"
        mock_response = MagicMock()
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)
        await middleware.dispatch(mock_request, call_next)
        assert len(mock_response.headers) == 0

    @pytest.mark.asyncio
    async def test_path_prefix_matching(self):
        """Test excluded path uses prefix matching"""
        middleware = SecurityHeadersMiddleware(
            app=MagicMock(),
            exclude_paths=["/api/internal"],
        )
        mock_request = MagicMock()
        mock_request.url.path = "/api/internal/v1/health"
        mock_response = MagicMock()
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)
        await middleware.dispatch(mock_request, call_next)
        assert len(mock_response.headers) == 0

    @pytest.mark.asyncio
    async def test_non_excluded_path_gets_headers(self):
        """Test non-excluded path gets headers"""
        middleware = SecurityHeadersMiddleware(
            app=MagicMock(),
            exclude_paths=["/health"],
        )
        mock_request = MagicMock()
        mock_request.url.path = "/api/users"
        mock_response = MagicMock()
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)
        await middleware.dispatch(mock_request, call_next)
        assert len(mock_response.headers) > 0

    def test_custom_referrer_policy(self):
        """Test custom referrer policy"""
        config = SecurityHeadersConfig(referrer_policy="no-referrer")
        assert config.referrer_policy == "no-referrer"

    def test_custom_permissions_policy(self):
        """Test custom permissions policy"""
        config = SecurityHeadersConfig(
            permissions_policy="camera=(), microphone=()",
        )
        assert "camera=()" in config.permissions_policy

    def test_custom_xss_protection(self):
        """Test custom XSS protection"""
        config = SecurityHeadersConfig(x_xss_protection="0")
        assert config.x_xss_protection == "0"
