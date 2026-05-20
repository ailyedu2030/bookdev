"""
F01: 不可变日志系统 - GREEN阶段实现

按照TDD原则，此实现仅包含让测试通过的最简代码。
优化和重构将在Refactor阶段进行。
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


class ImmutableLogError(Exception):
    """不可变日志系统异常"""
    pass


@dataclass(frozen=True)
class LogEntry:
    """
    不可变日志条目

    特性:
    - 使用frozen dataclass确保不可变
    - version_tag: SHA-256哈希，包含内容+前驱哈希
    - content_hash: 内容的SHA-256哈希
    - timestamp: UTC时间戳
    - operation_type: 操作类型
    - payload: 原始数据
    - previous_hash: 前驱条目的version_tag
    """
    version_tag: str
    content_hash: str
    timestamp: datetime
    operation_type: str
    payload: dict
    previous_hash: Optional[str]

    def modify(self, new_payload: dict) -> None:
        """
        尝试修改日志条目

        抛出:
            ImmutableLogError: 总是抛出，因为日志不可变
        """
        raise ImmutableLogError("Log entries are immutable and cannot be modified")


class ImmutableLog:
    """
    不可变日志链

    特性:
    - 链式结构，每个条目包含指向前驱的哈希
    - 支持完整性验证
    - 追加操作返回新条目
    """

    def __init__(self):
        self._entries: list[LogEntry] = []
        self._chain_hash: Optional[str] = None

    def append(self, operation_type: str, payload: dict) -> LogEntry:
        """
        追加新日志条目

        Args:
            operation_type: 操作类型标识
            payload: 要记录的数据

        Returns:
            LogEntry: 新创建的日志条目
        """
        content_json = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        content_bytes = content_json.encode('utf-8')
        content_hash = hashlib.sha256(content_bytes).hexdigest()

        version_input = content_hash + (self._chain_hash or "")
        version_tag = hashlib.sha256(version_input.encode('utf-8')).hexdigest()

        entry = LogEntry(
            version_tag=version_tag,
            content_hash=content_hash,
            timestamp=datetime.utcnow(),
            operation_type=operation_type,
            payload=payload,
            previous_hash=self._chain_hash
        )

        self._entries.append(entry)
        self._chain_hash = version_tag

        return entry

    def get_entries(self) -> list[LogEntry]:
        """获取所有日志条目"""
        return self._entries.copy()

    def get_latest_hash(self) -> Optional[str]:
        """获取最新条目的版本戳"""
        if not self._entries:
            return None
        return self._entries[-1].version_tag


# 全局链状态(用于create_log_entry的链式调用)
_global_chain_hash: Optional[str] = None


def create_log_entry(
    operation_type: str,
    payload: dict,
    previous_hash: Optional[str] = None
) -> LogEntry:
    """
    创建单个日志条目的便捷函数

    支持链式创建：多次调用create_log_entry会形成链式结构。

    Args:
        operation_type: 操作类型
        payload: 日志数据
        previous_hash: 前驱条目的version_tag（可选，默认自动维护全局链）

    Returns:
        LogEntry: 新日志条目
    """
    global _global_chain_hash

    content_json = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    content_bytes = content_json.encode('utf-8')
    content_hash = hashlib.sha256(content_bytes).hexdigest()

    # 如果没有提供previous_hash，使用全局链状态
    prev_hash = previous_hash if previous_hash is not None else _global_chain_hash

    version_input = content_hash + (prev_hash or "")
    version_tag = hashlib.sha256(version_input.encode('utf-8')).hexdigest()

    # 更新全局链状态
    _global_chain_hash = version_tag

    return LogEntry(
        version_tag=version_tag,
        content_hash=content_hash,
        timestamp=datetime.utcnow(),
        operation_type=operation_type,
        payload=payload,
        previous_hash=prev_hash
    )


def reset_global_chain() -> None:
    """重置全局链状态（主要用于测试）"""
    global _global_chain_hash
    _global_chain_hash = None


def verify_chain_integrity(entries: list[LogEntry]) -> bool:
    """
    验证日志链完整性

    检查:
    1. 每个条目的previous_hash是否指向前一个条目的version_tag
    2. 链的连续性是否被破坏

    Args:
        entries: 日志条目列表

    Returns:
        bool: 完整性验证通过返回True，否则返回False
    """
    if len(entries) <= 1:
        return True

    for i in range(1, len(entries)):
        if entries[i].previous_hash != entries[i - 1].version_tag:
            return False

    return True