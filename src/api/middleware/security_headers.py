"""
Security Headers Middleware

Adds security headers to all responses:
- HSTS (HTTP Strict Transport Security)
- CSP (Content Security Policy)
- X-Frame-Options
- X-Content-Type-Options
- Referrer-Policy
- Permissions-Policy
- X-XSS-Protection
"""

from typing import Callable, List, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersConfig:
    """Configuration for security headers"""

    def __init__(
        self,
        hsts_max_age: int = 31536000,
        hsts_include_subdomains: bool = True,
        hsts_preload: bool = True,
        csp_default_src: str = "'self'",
        csp_script_src: str = "'self' 'unsafe-inline'",
        csp_style_src: str = "'self' 'unsafe-inline'",
        csp_img_src: str = "'self' data: https:",
        csp_connect_src: str = "'self' https://api.minimaxi.com",
        csp_frame_ancestors: str = "'none'",
        x_frame_options: str = "DENY",
        x_content_type_options: str = "nosniff",
        referrer_policy: str = "strict-origin-when-cross-origin",
        permissions_policy: str = "accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()",
        x_xss_protection: str = "1; mode=block",
    ):
        self.hsts_max_age = hsts_max_age
        self.hsts_include_subdomains = hsts_include_subdomains
        self.hsts_preload = hsts_preload
        self.csp_default_src = csp_default_src
        self.csp_script_src = csp_script_src
        self.csp_style_src = csp_style_src
        self.csp_img_src = csp_img_src
        self.csp_connect_src = csp_connect_src
        self.csp_frame_ancestors = csp_frame_ancestors
        self.x_frame_options = x_frame_options
        self.x_content_type_options = x_content_type_options
        self.referrer_policy = referrer_policy
        self.permissions_policy = permissions_policy
        self.x_xss_protection = x_xss_protection

    def get_hsts_header(self) -> str:
        """Generate HSTS header value"""
        value = f"max-age={self.hsts_max_age}"
        if self.hsts_include_subdomains:
            value += "; includeSubDomains"
        if self.hsts_preload:
            value += "; preload"
        return value

    def get_csp_header(self) -> str:
        """Generate CSP header value"""
        parts = [
            f"default-src {self.csp_default_src}",
            f"script-src {self.csp_script_src}",
            f"style-src {self.csp_style_src}",
            f"img-src {self.csp_img_src}",
            f"connect-src {self.csp_connect_src}",
            f"frame-ancestors {self.csp_frame_ancestors}",
        ]
        return "; ".join(parts)


DEFAULT_SECURITY_CONFIG = SecurityHeadersConfig()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds security headers to all responses.
    """

    def __init__(
        self,
        app,
        config: SecurityHeadersConfig = None,
        exclude_paths: List[str] = None,
    ):
        super().__init__(app)
        self.config = config or DEFAULT_SECURITY_CONFIG
        self.exclude_paths = exclude_paths or []

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path

        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                return await call_next(request)

        response = await call_next(request)

        response.headers["Strict-Transport-Security"] = self.config.get_hsts_header()
        response.headers["Content-Security-Policy"] = self.config.get_csp_header()
        response.headers["X-Frame-Options"] = self.config.x_frame_options
        response.headers["X-Content-Type-Options"] = self.config.x_content_type_options
        response.headers["Referrer-Policy"] = self.config.referrer_policy
        response.headers["Permissions-Policy"] = self.config.permissions_policy
        response.headers["X-XSS-Protection"] = self.config.x_xss_protection

        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"

        return response
