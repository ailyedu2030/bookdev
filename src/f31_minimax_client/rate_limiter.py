"""
F31: MiniMax M2.7 API客户端 - 速率限制器

基于滑动窗口的请求速率限制，支持同步检查和异步等待。
"""

import asyncio
import time
from threading import Lock


class RateLimiter:
    """
    滑动窗口速率限制器

    INF-013: Separated 'check' and 'record' operations to prevent
   虚假计数 when check passes but no actual request is sent.
    """

    def __init__(self, max_rpm: int = 60):
        """
        初始化速率限制器

        Args:
            max_rpm: 每分钟最大请求数
        """
        self.max_rpm = max_rpm
        self._lock = Lock()
        self._request_timestamps: list[float] = []
        self._window_seconds = 60.0
        self._window_start = time.monotonic()

    def _clean_old_timestamps(self) -> None:
        """Clean expired timestamps from the window"""
        now = time.monotonic()
        cutoff = now - self._window_seconds
        self._request_timestamps = [
            ts for ts in self._request_timestamps if ts > cutoff
        ]

    def can_proceed(self) -> bool:
        """
        Check if a request can proceed WITHOUT recording.

        This is a pure check operation - use request_recorded() to
        actually record a request after it succeeds.

        Returns:
            True if request can proceed, False otherwise
        """
        with self._lock:
            self._clean_old_timestamps()
            return len(self._request_timestamps) < self.max_rpm

    def request_recorded(self) -> bool:
        """
        Record that a request was actually made.

        Call this AFTER a request is confirmed to have been sent,
        not before can_proceed() check.

        Returns:
            True if recorded successfully, False if limit would be exceeded
        """
        with self._lock:
            self._clean_old_timestamps()
            if len(self._request_timestamps) < self.max_rpm:
                self._request_timestamps.append(time.monotonic())
                return True
            return False

    def check_and_record(self) -> bool:
        """
        Combined check + record for convenience.

        Use this when you immediately make a request after checking.
        For more complex flows, use can_proceed() + request_recorded() separately.

        Returns:
            True if check passed and request was recorded
        """
        with self._lock:
            self._clean_old_timestamps()
            if len(self._request_timestamps) < self.max_rpm:
                self._request_timestamps.append(time.monotonic())
                return True
            return False

    def remaining(self) -> int:
        """
        获取当前窗口内剩余请求数

        Returns:
            剩余可用请求数
        """
        with self._lock:
            self._clean_old_timestamps()
            return max(0, self.max_rpm - len(self._request_timestamps))

    async def wait_for_available(self, timeout: float = 60.0) -> bool:
        """
        异步等待直到有可用配额

        Args:
            timeout: 最大等待时间(秒)

        Returns:
            True如果获取到配额，False如果超时
        """
        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            if self.check_and_record():
                return True
            # 计算需要等待的时间
            with self._lock:
                self._clean_old_timestamps()
                if self._request_timestamps:
                    oldest = min(self._request_timestamps)
                    wait = oldest + self._window_seconds - time.monotonic()
                    wait = max(0.1, min(wait, 10.0))
                else:
                    wait = 0.1
            await asyncio.sleep(wait)

        return False
