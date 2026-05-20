"""
F31: MiniMax M2.7 API客户端 - 成本追踪器

追踪API调用次数、Token使用量和成本。
"""

import time
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class UsageStats:
    """使用统计"""
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    total_calls: int = 0
    total_cost: float = 0.0
    first_call_at: float = 0.0
    last_call_at: float = 0.0
    avg_tokens_per_call: float = 0.0

    def to_dict(self) -> dict:
        return {
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_tokens,
            "total_calls": self.total_calls,
            "total_cost": self.total_cost,
            "first_call_at": datetime.fromtimestamp(self.first_call_at).isoformat() if self.first_call_at else None,
            "last_call_at": datetime.fromtimestamp(self.last_call_at).isoformat() if self.last_call_at else None,
            "avg_tokens_per_call": round(self.avg_tokens_per_call, 2),
        }


class CostTracker:
    """成本追踪器"""

    def __init__(self, price_per_million: float = 2.0):
        """
        初始化成本追踪器

        Args:
            price_per_million: 每百万Token的价格(¥)
        """
        self.price_per_million = price_per_million
        self._prompt_tokens = 0
        self._completion_tokens = 0
        self._call_count = 0
        self._first_call_at = 0.0
        self._last_call_at = 0.0

    def record_usage(self, prompt_tokens: int, completion_tokens: int):
        """
        记录一次API调用

        Args:
            prompt_tokens: 提示Token数
            completion_tokens: 完成Token数
        """
        self._prompt_tokens += prompt_tokens
        self._completion_tokens += completion_tokens
        self._call_count += 1

        now = time.time()
        if self._first_call_at == 0.0:
            self._first_call_at = now
        self._last_call_at = now

    def get_stats(self) -> UsageStats:
        """
        获取使用统计

        Returns:
            UsageStats对象
        """
        total_tokens = self._prompt_tokens + self._completion_tokens
        cost = (total_tokens / 1_000_000) * self.price_per_million
        avg_tokens = total_tokens / max(1, self._call_count)

        return UsageStats(
            total_prompt_tokens=self._prompt_tokens,
            total_completion_tokens=self._completion_tokens,
            total_tokens=total_tokens,
            total_calls=self._call_count,
            total_cost=cost,
            first_call_at=self._first_call_at,
            last_call_at=self._last_call_at,
            avg_tokens_per_call=avg_tokens,
        )

    def reset(self):
        """重置所有统计"""
        self._prompt_tokens = 0
        self._completion_tokens = 0
        self._call_count = 0
        self._first_call_at = 0.0
        self._last_call_at = 0.0
