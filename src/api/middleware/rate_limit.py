"""
Rate Limiting Middleware

Implements in-memory sliding window rate limiting.
"""

import time
from collections.abc import Callable
from dataclasses import dataclass, field

from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


@dataclass
class RateLimitConfig:
    """Rate limit configuration for an endpoint"""
    requests: int
    window_seconds: int
    key_prefix: str = "rl"


@dataclass
class RateLimitSettings:
    """Global rate limit settings"""
    trust_x_forwarded_for: bool = False
    trust_x_real_ip: bool = False


@dataclass
class SlidingWindowEntry:
    """Sliding window entry for rate limiting"""
    timestamps: list[float] = field(default_factory=list)


class InMemoryRateLimiter:
    """
    In-memory sliding window rate limiter.

    Uses a dictionary of lists to track request timestamps
    for each unique key (typically IP address or user ID).
    """

    def __init__(self):
        self._storage: dict[str, SlidingWindowEntry] = {}
        self._cleanup_interval = 3600
        self._last_cleanup = time.time()

    def _cleanup_expired(self, current_time: float) -> None:
        """Remove expired entries to prevent memory growth"""
        if current_time - self._last_cleanup < self._cleanup_interval:
            return

        expired_keys = []
        for key, entry in self._storage.items():
            entry.timestamps = [
                ts for ts in entry.timestamps
                if current_time - ts < 3600
            ]
            if not entry.timestamps:
                expired_keys.append(key)

        for key in expired_keys:
            del self._storage[key]

        self._last_cleanup = current_time

    async def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> tuple[bool, int, int]:
        """
        Check if request is within rate limit.

        Returns:
            Tuple of (allowed, remaining, reset_time)
        """
        current_time = time.time()
        self._cleanup_expired(current_time)

        if key not in self._storage:
            self._storage[key] = SlidingWindowEntry()

        entry = self._storage[key]

        cutoff_time = current_time - window_seconds
        entry.timestamps = [ts for ts in entry.timestamps if ts > cutoff_time]

        if len(entry.timestamps) >= max_requests:
            oldest_timestamp = min(entry.timestamps)
            reset_time = int(oldest_timestamp + window_seconds - current_time)
            return False, 0, reset_time

        entry.timestamps.append(current_time)
        remaining = max_requests - len(entry.timestamps)
        reset_time = int(entry.timestamps[0] + window_seconds - current_time)

        return True, remaining, reset_time


rate_limiter = InMemoryRateLimiter()


DEFAULT_RATE_LIMITS: dict[str, RateLimitConfig] = {
    "anonymous": RateLimitConfig(requests=30, window_seconds=60, key_prefix="anon"),
    "authenticated": RateLimitConfig(requests=300, window_seconds=60, key_prefix="auth"),
    "strict": RateLimitConfig(requests=10, window_seconds=60, key_prefix="strict"),
    "auth_login": RateLimitConfig(requests=5, window_seconds=60, key_prefix="login"),
    "auth_register": RateLimitConfig(requests=3, window_seconds=3600, key_prefix="register"),
    "scan": RateLimitConfig(requests=30, window_seconds=60, key_prefix="scan"),
    "generate": RateLimitConfig(requests=10, window_seconds=3600, key_prefix="generate"),
}


rate_limit_settings = RateLimitSettings(
    trust_x_forwarded_for=False,
    trust_x_real_ip=False,
)


def get_client_identifier(request: Request) -> str:
    """Get unique identifier for rate limiting"""
    if rate_limit_settings.trust_x_forwarded_for:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

    if rate_limit_settings.trust_x_real_ip:
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

    if request.client:
        return request.client.host

    return "unknown"


def rate_limit(
    config: RateLimitConfig = None,
    key_func: Callable[[Request], str] = None,
):
    """
    Dependency for endpoint-level rate limiting.

    Usage:
        @router.post("/items")
        @rate_limit(RateLimitConfig(requests=100, window_seconds=60))
        async def create_item(request: Request):
            ...
    """
    if config is None:
        config = DEFAULT_RATE_LIMITS["authenticated"]

    async def dependency(request: Request) -> None:
        client_key = key_func(request) if key_func else get_client_identifier(request)
        rate_key = f"{config.key_prefix}:{client_key}"

        allowed, remaining, reset = await rate_limiter.check_rate_limit(
            rate_key,
            config.requests,
            config.window_seconds,
        )

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"Rate limit exceeded. Try again in {reset} seconds.",
                        "retry_after": reset,
                    }
                },
                headers={"Retry-After": str(reset)},
            )

    return dependency


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Global rate limiting middleware.

    Applies rate limiting based on client IP address.
    """

    def __init__(
        self,
        app,
        config: RateLimitConfig = None,
        exempt_paths: list[str] = None,
    ):
        super().__init__(app)
        self.config = config or DEFAULT_RATE_LIMITS["anonymous"]
        self.exempt_paths = exempt_paths or ["/api/monitor/health", "/docs", "/openapi.json"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path

        for exempt_path in self.exempt_paths:
            if path.startswith(exempt_path):
                return await call_next(request)

        client_key = get_client_identifier(request)
        rate_key = f"{self.config.key_prefix}:{client_key}"

        allowed, remaining, reset = await rate_limiter.check_rate_limit(
            rate_key,
            self.config.requests,
            self.config.window_seconds,
        )

        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "success": False,
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"Rate limit exceeded. Try again in {reset} seconds.",
                        "retry_after": reset,
                    },
                },
                headers={
                    "Retry-After": str(reset),
                    "X-RateLimit-Limit": str(self.config.requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset),
                },
            )

        response = await call_next(request)

        response.headers["X-RateLimit-Limit"] = str(self.config.requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset)

        return response
