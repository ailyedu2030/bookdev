"""
F03: 内容寻址哈希系统 - GREEN阶段实现

Token位置稳定化（内容寻址）
"""

import hashlib
from dataclasses import dataclass


def calculate_content_hash(content: str, offset: int = 0) -> str:
    """
    计算内容的SHA-256哈希

    内容寻址哈希与位置无关，相同内容总是产生相同的哈希值。

    Args:
        content: 要哈希的内容
        offset: 位置偏移（被忽略，保持API兼容性）

    Returns:
        str: SHA-256十六进制哈希字符串
    """
    content_bytes = content.encode('utf-8')
    return hashlib.sha256(content_bytes).hexdigest()


@dataclass
class ContentAddressReference:
    """
    内容地址引用

    用于引用特定内容片段，包含内容哈希和位置信息。
    """
    content_hash: str
    offset: int
    length: int

    def to_string(self) -> str:
        """转换为字符串表示"""
        return "{hash: " + self.content_hash + ", offset: " + str(self.offset) + ", length: " + str(self.length) + "}"

    def __eq__(self, other) -> bool:
        if not isinstance(other, ContentAddressReference):
            return False
        return (
            self.content_hash == other.content_hash and
            self.offset == other.offset and
            self.length == other.length
        )


def create_reference_from_content(content: str, offset: int = 0) -> ContentAddressReference:
    """
    从内容创建引用

    Args:
        content: 内容
        offset: 起始偏移

    Returns:
        ContentAddressReference: 内容地址引用
    """
    content_hash = calculate_content_hash(content)
    return ContentAddressReference(
        content_hash=content_hash,
        offset=offset,
        length=len(content)
    )


def verify_integrity(content: str, stored_hash: str) -> bool:
    """
    验证内容完整性

    Args:
        content: 要验证的内容
        stored_hash: 存储的哈希值

    Returns:
        bool: 验证通过返回True，否则返回False
    """
    computed_hash = calculate_content_hash(content)
    return computed_hash == stored_hash


def deduplicate_by_hash(contents: list[str]) -> list[str]:
    """
    通过哈希去重

    保留首次出现的内容顺序。

    Args:
        contents: 内容列表

    Returns:
        list[str]: 去重后的内容列表
    """
    seen_hashes = set()
    result = []

    for content in contents:
        content_hash = calculate_content_hash(content)
        if content_hash not in seen_hashes:
            seen_hashes.add(content_hash)
            result.append(content)

    return result