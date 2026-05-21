"""
CSRF Protection Middleware

Implements double-submit cookie pattern for CSRF protection.
"""

import hashlib
import secrets
import time
from collections.abc import Callable

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

CSRF_TOKEN_COOKIE_NAME = "csrf_token"
CSRF_TOKEN_HEADER_NAME = "X-CSRF-Token"
CSRF_TOKEN_REQUEST_HEADER_NAME = "x-csrf-token"
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


class CSRFTokenManager:
    """Manages CSRF tokens for the double-submit pattern"""

    def __init__(self, secret_key: str = None):
        self.secret_key = secret_key or secrets.token_hex(32)
        self._token_cache = {}

    def generate_token(self) -> str:
        """Generate a new CSRF token"""
        token = secrets.token_hex(32)
        timestamp = int(time.time())
        signature = self._sign_token(token, timestamp)
        return f"{token}.{timestamp}.{signature}"

    def _sign_token(self, token: str, timestamp: int) -> str:
        """Create HMAC signature for token"""
        message = f"{token}.{timestamp}"
        return hashlib.sha256(f"{self.secret_key}:{message}".encode()).hexdigest()[:16]

    def validate_token(self, token: str) -> bool:
        """Validate a CSRF token"""
        if not token:
            return False

        try:
            parts = token.split(".")
            if len(parts) != 3:
                return False

            token_value, timestamp_str, signature = parts
            timestamp = int(timestamp_str)

            expected_signature = self._sign_token(token_value, timestamp)
            if not secrets.compare_digest(signature, expected_signature):
                return False

            if timestamp < int(time.time()) - 3600:
                return False

            return True

        except (ValueError, IndexError):
            return False

    def extract_token_from_header(self, request: Request) -> str | None:
        """Extract CSRF token from request header"""
        return request.headers.get(CSRF_TOKEN_HEADER_NAME) or request.headers.get(CSRF_TOKEN_REQUEST_HEADER_NAME)

    def extract_token_from_cookie(self, request: Request) -> str | None:
        """Extract CSRF token from cookies"""
        return request.cookies.get(CSRF_TOKEN_COOKIE_NAME)


csrf_token_manager = CSRFTokenManager()


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF protection middleware using double-submit cookie pattern.

    For state-changing operations (POST, PUT, PATCH, DELETE),
    validates that the CSRF token in the header matches the token in the cookie.
    """

    def __init__(
        self,
        app,
        token_manager: CSRFTokenManager = None,
        safe_paths: list[str] = None,
        exclude_paths: list[str] = None,
    ):
        super().__init__(app)
        self.token_manager = token_manager or csrf_token_manager
        self.safe_paths = safe_paths or ["/api/monitor/health", "/docs", "/openapi.json"]
        self.exclude_paths = exclude_paths or []

    def _is_path_safe(self, path: str) -> bool:
        """Check if path is safe (doesn't require CSRF)"""
        for safe_path in self.safe_paths:
            if path.startswith(safe_path):
                return True
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                return True
        return False

    def _is_state_changing(self, method: str) -> bool:
        """Check if request method is state-changing"""
        return method not in SAFE_METHODS

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path

        if self._is_path_safe(path):
            return await call_next(request)

        if self._is_state_changing(request.method):
            cookie_token = self.token_manager.extract_token_from_cookie(request)
            header_token = self.token_manager.extract_token_from_header(request)

            if not cookie_token or not header_token:
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={
                        "success": False,
                        "error": {
                            "code": "CSRF_TOKEN_MISSING",
                            "message": "CSRF token is required for this operation",
                        },
                    },
                )

            if not self.token_manager.validate_token(cookie_token):
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={
                        "success": False,
                        "error": {
                            "code": "CSRF_TOKEN_INVALID",
                            "message": "Invalid or expired CSRF token",
                        },
                    },
                )

            if cookie_token != header_token:
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={
                        "success": False,
                        "error": {
                            "code": "CSRF_TOKEN_MISMATCH",
                            "message": "CSRF token mismatch",
                        },
                    },
                )

        response = await call_next(request)

        if self._is_state_changing(request.method):
            csrf_token = self.token_manager.generate_token()
            response.set_cookie(
                key=CSRF_TOKEN_COOKIE_NAME,
                value=csrf_token,
                httponly=True,
                secure=True,
                samesite="strict",
                max_age=3600,
            )

        return response


async def csrf_protect(request: Request) -> None:
    """
    Dependency for endpoint-level CSRF protection.

    Usage:
        @router.post("/items")
        async def create_item(request: Request, _: None = Depends(csrf_protect)):
            ...
    """
    if request.method in SAFE_METHODS:
        return

    cookie_token = csrf_token_manager.extract_token_from_cookie(request)
    header_token = csrf_token_manager.extract_token_from_header(request)

    if not cookie_token or not header_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "CSRF_TOKEN_MISSING",
                    "message": "CSRF token is required for this operation",
                }
            },
        )

    if not csrf_token_manager.validate_token(cookie_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "CSRF_TOKEN_INVALID",
                    "message": "Invalid or expired CSRF token",
                }
            },
        )

    if cookie_token != header_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "CSRF_TOKEN_MISMATCH",
                    "message": "CSRF token mismatch",
                }
            },
        )
