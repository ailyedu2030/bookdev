"""
F01: 不可变日志系统 - TDD RED阶段测试

本测试文件包含所有RED测试用例，这些测试在实现前应该失败。
按照TDD原则：
1. RED: 写失败测试 (本文件)
2. GREEN: 写最简实现让测试通过
3. Refactor: 优化代码质量
"""

import hashlib
from datetime import datetime

import pytest


@pytest.fixture(autouse=True)
def reset_chain():
    """每个测试前重置全局链状态"""
    from f01_immutable_log import immutable_log
    immutable_log.reset_global_chain()
    yield
    immutable_log.reset_global_chain()


class TestImmutableLogEntry:
    """不可变日志条目基础测试"""

    def test_log_entry_must_have_version_tag(self):
        """F01-T001: 日志条目必须有版本戳 (SHA-256)"""
        from f01_immutable_log.immutable_log import create_log_entry

        log_entry = create_log_entry("llm_call", {"prompt": "test"})

        assert log_entry.version_tag is not None
        assert len(log_entry.version_tag) == 64  # SHA-256 hex length
        # 版本戳应该是十六进制字符串
        assert all(c in '0123456789abcdef' for c in log_entry.version_tag)

    def test_log_entry_must_have_content_hash(self):
        """F01-T002: 日志条目必须有内容哈希"""
        from f01_immutable_log.immutable_log import create_log_entry

        log_entry = create_log_entry("llm_call", {"prompt": "test"})

        assert log_entry.content_hash is not None
        assert len(log_entry.content_hash) == 64  # SHA-256 hex length
        # 内容哈希应基于实际内容计算
        expected_content = b'{"prompt": "test"}'
        expected_hash = hashlib.sha256(expected_content).hexdigest()
        assert log_entry.content_hash == expected_hash

    def test_log_entry_content_hash_is_deterministic(self):
        """F01-T002b: 相同内容产生相同哈希"""
        from f01_immutable_log.immutable_log import create_log_entry

        entry1 = create_log_entry("call_1", {"data": "hello"})
        entry2 = create_log_entry("call_2", {"data": "hello"})

        assert entry1.content_hash == entry2.content_hash

    def test_log_immutability_cannot_be_modified(self):
        """F01-T003: 日志不可修改"""
        from f01_immutable_log.immutable_log import ImmutableLogError, create_log_entry

        log_entry = create_log_entry("llm_call", {"prompt": "test"})

        with pytest.raises(ImmutableLogError):
            log_entry.modify({"prompt": "modified"})

    def test_log_entry_has_timestamp(self):
        """F01-T004: 日志条目必须有不可变时间戳"""
        from f01_immutable_log.immutable_log import create_log_entry

        log_entry = create_log_entry("llm_call", {"prompt": "test"})

        assert log_entry.timestamp is not None
        assert isinstance(log_entry.timestamp, datetime)

    def test_log_entry_has_operation_type(self):
        """F01-T004b: 日志条目必须有操作类型"""
        from f01_immutable_log.immutable_log import create_log_entry

        log_entry = create_log_entry("llm_call", {"prompt": "test"})

        assert log_entry.operation_type == "llm_call"

    def test_log_entry_has_payload(self):
        """F01-T004c: 日志条目必须包含原始payload"""
        from f01_immutable_log.immutable_log import create_log_entry

        payload = {"prompt": "test", "model": "gpt-4"}
        log_entry = create_log_entry("llm_call", payload)

        assert log_entry.payload == payload

    def test_log_entry_has_previous_hash(self):
        """F01-T004d: 日志条目包含前驱哈希(链式结构)"""
        from f01_immutable_log.immutable_log import create_log_entry

        entry1 = create_log_entry("call_1", {"data": "first"})
        entry2 = create_log_entry("call_2", {"data": "second"})

        # 第一个条目没有前驱哈希
        assert entry1.previous_hash is None
        # 第二个条目的前驱哈希指向前一个条目
        assert entry2.previous_hash == entry1.version_tag


class TestImmutableLogChain:
    """不可变日志链完整性测试"""

    def test_chain_integrity_verification_passes(self):
        """F01-T005: 链完整性验证 - 正常链"""
        from f01_immutable_log.immutable_log import create_log_entry, verify_chain_integrity

        entries = [
            create_log_entry("call_1", {"data": "a"}),
            create_log_entry("call_2", {"data": "b"}),
        ]

        assert verify_chain_integrity(entries) is True

    def test_chain_integrity_verification_single_entry(self):
        """F01-T005b: 单条目链总是有效的"""
        from f01_immutable_log.immutable_log import create_log_entry, verify_chain_integrity

        entries = [create_log_entry("call_1", {"data": "a"})]
        assert verify_chain_integrity(entries) is True

    def test_chain_integrity_verification_empty_chain(self):
        """F01-T005c: 空链应该返回True"""
        from f01_immutable_log.immutable_log import verify_chain_integrity

        assert verify_chain_integrity([]) is True

    def test_detect_tampering_in_history(self):
        """F01-T006: 检测历史篡改 - 创建假链"""
        from f01_immutable_log.immutable_log import LogEntry, create_log_entry, verify_chain_integrity

        entries = [
            create_log_entry("call_1", {"data": "a"}),
            create_log_entry("call_2", {"data": "b"}),
        ]

        # 创建包含假previous_hash的链来模拟篡改
        # 由于LogEntry不可变，我们通过重新创建条目来模拟攻击场景
        fake_entry = LogEntry(
            version_tag="fake_version",
            content_hash="tampered_hash",
            timestamp=datetime.utcnow(),
            operation_type="call_1",
            payload={"data": "a"},
            previous_hash="fake_previous"  # 错误的previous_hash
        )

        # 用假条目替换第一个条目
        tampered_entries = [fake_entry, entries[1]]

        # 验证应该失败
        assert verify_chain_integrity(tampered_entries) is False

    def test_detect_chain_break(self):
        """F01-T006b: 检测链断裂"""
        from f01_immutable_log.immutable_log import LogEntry, create_log_entry, verify_chain_integrity

        entry1 = create_log_entry("call_1", {"data": "a"})
        entry2 = create_log_entry("call_2", {"data": "b"})

        # 创建有正确previous_hash的链（正常）
        assert verify_chain_integrity([entry1, entry2]) is True

        # 创建断裂的链
        broken_entry2 = LogEntry(
            version_tag=entry2.version_tag,
            content_hash=entry2.content_hash,
            timestamp=entry2.timestamp,
            operation_type=entry2.operation_type,
            payload=entry2.payload,
            previous_hash="fake_previous_hash"  # 错误的previous_hash
        )

        assert verify_chain_integrity([entry1, broken_entry2]) is False

    def test_detect_version_tag_tampering(self):
        """F01-T006c: 检测版本戳被篡改"""
        from f01_immutable_log.immutable_log import LogEntry, create_log_entry, verify_chain_integrity

        entry1 = create_log_entry("call_1", {"data": "a"})
        entry2 = create_log_entry("call_2", {"data": "b"})

        # 正常链应该通过
        assert verify_chain_integrity([entry1, entry2]) is True

        # 创建版本戳被篡改的条目
        tampered_entry1 = LogEntry(
            version_tag="tampered_version_tag",  # 篡改版本戳
            content_hash=entry1.content_hash,
            timestamp=entry1.timestamp,
            operation_type=entry1.operation_type,
            payload=entry1.payload,
            previous_hash=entry1.previous_hash
        )

        tampered_entries = [tampered_entry1, entry2]
        assert verify_chain_integrity(tampered_entries) is False


class TestImmutableLogClass:
    """ImmutableLog类测试"""

    def test_immutable_log_starts_empty(self):
        """F01-T007: 日志链初始为空"""
        from f01_immutable_log.immutable_log import ImmutableLog

        log = ImmutableLog()
        assert log.get_entries() == []

    def test_immutable_log_append_returns_entry(self):
        """F01-T007b: append操作返回日志条目"""
        from f01_immutable_log.immutable_log import ImmutableLog

        log = ImmutableLog()
        entry = log.append("test_operation", {"key": "value"})

        assert entry is not None
        assert entry.operation_type == "test_operation"
        assert entry.payload == {"key": "value"}

    def test_immutable_log_entries_persisted(self):
        """F01-T007c: append后条目被持久化"""
        from f01_immutable_log.immutable_log import ImmutableLog

        log = ImmutableLog()
        log.append("op1", {"data": "a"})
        log.append("op2", {"data": "b"})

        entries = log.get_entries()
        assert len(entries) == 2
        assert entries[0].operation_type == "op1"
        assert entries[1].operation_type == "op2"

    def test_immutable_log_chain_hash_continuity(self):
        """F01-T007d: 链哈希连续性"""
        from f01_immutable_log.immutable_log import ImmutableLog

        log = ImmutableLog()
        entry1 = log.append("op1", {"data": "a"})
        entry2 = log.append("op2", {"data": "b"})

        assert entry1.previous_hash is None
        assert entry2.previous_hash == entry1.version_tag

    def test_immutable_log_cannot_modify_entry(self):
        """F01-T007e: 无法直接修改已有条目"""
        from f01_immutable_log.immutable_log import ImmutableLog, ImmutableLogError

        log = ImmutableLog()
        entry = log.append("op1", {"data": "a"})

        with pytest.raises(ImmutableLogError):
            entry.modify({"data": "modified"})

    def test_immutable_log_get_latest_hash(self):
        """F01-T007f: 获取最新哈希"""
        from f01_immutable_log.immutable_log import ImmutableLog

        log = ImmutableLog()
        log.append("op1", {"data": "a"})
        entry2 = log.append("op2", {"data": "b"})

        assert log.get_latest_hash() == entry2.version_tag

    def test_immutable_log_empty_get_latest_hash(self):
        """F01-T007g: 空日志获取最新哈希返回None"""
        from f01_immutable_log.immutable_log import ImmutableLog

        log = ImmutableLog()
        assert log.get_latest_hash() is None


class TestImmutableLogSecurity:
    """不可变日志安全测试"""

    def test_version_tag_includes_previous_hash(self):
        """F01-T008: 版本戳包含前驱哈希(防止链伪造)"""
        from f01_immutable_log.immutable_log import ImmutableLog

        log = ImmutableLog()
        entry1 = log.append("op1", {"data": "a"})
        entry2 = log.append("op2", {"data": "b"})

        # 版本戳应该依赖于前驱哈希
        assert entry2.version_tag != entry1.version_tag
        # 不同的前驱会导致不同的版本戳
        entry1_different = log.append("op1", {"data": "different"})
        assert entry1_different.version_tag != entry1.version_tag

    def test_identical_content_different_position_different_version(self):
        """F01-T008b: 相同内容在不同位置产生不同版本"""
        from f01_immutable_log.immutable_log import ImmutableLog

        log = ImmutableLog()
        entry1 = log.append("op1", {"data": "same"})
        entry2 = log.append("op2", {"data": "same"})

        # 相同内容，但由于位置不同，版本戳不同
        assert entry1.version_tag != entry2.version_tag
        # 但内容哈希应该相同
        assert entry1.content_hash == entry2.content_hash

    def test_log_entry_immutability_via_dataclass(self):
        """F01-T008c: 使用dataclass实现不可变性"""
        from f01_immutable_log.immutable_log import create_log_entry

        entry = create_log_entry("test", {"key": "value"})

        # 尝试通过任何方式修改都应该失败
        with pytest.raises((AttributeError, TypeError)):
            entry.version_tag = "tampered"

    def test_hash_collision_resistance(self):
        """F01-T008d: 哈希碰撞抵抗(简单测试)"""
        from f01_immutable_log.immutable_log import create_log_entry

        # 不同内容应该产生不同哈希
        entry1 = create_log_entry("op1", {"data": "test1"})
        entry2 = create_log_entry("op2", {"data": "test2"})

        assert entry1.content_hash != entry2.content_hash


class TestImmutableLogEdgeCases:
    """边界条件测试"""

    def test_empty_payload(self):
        """F01-T009: 空payload"""
        from f01_immutable_log.immutable_log import create_log_entry

        entry = create_log_entry("op", {})

        assert entry.payload == {}
        assert entry.content_hash is not None

    def test_large_payload(self):
        """F01-T009b: 大型payload"""
        from f01_immutable_log.immutable_log import create_log_entry

        large_data = {"data": "x" * 100000}
        entry = create_log_entry("op", large_data)

        assert entry.content_hash is not None
        assert len(entry.content_hash) == 64

    def test_unicode_payload(self):
        """F01-T009c: Unicode内容"""
        from f01_immutable_log.immutable_log import create_log_entry

        unicode_text = "人工智能是研究、开发用于模拟、延伸和扩展人的智能的理论、方法、技术..."
        entry = create_log_entry("llm_call", {"text": unicode_text})

        assert entry.content_hash is not None
        assert entry.payload["text"] == unicode_text

    def test_special_characters_in_payload(self):
        """F01-T009d: 特殊字符"""
        from f01_immutable_log.immutable_log import create_log_entry

        special_data = {
            "json": '{"key": "value"}',
            "newline": "line1\nline2",
            "quote": '他说："你好"',
            "emoji": "🚀🎓📚"
        }
        entry = create_log_entry("op", special_data)

        assert entry.payload == special_data
        assert entry.content_hash is not None

    def test_nested_payload(self):
        """F01-T009e: 嵌套数据结构"""
        from f01_immutable_log.immutable_log import create_log_entry

        nested_data = {
            "level1": {
                "level2": {
                    "level3": ["a", "b", "c"]
                }
            }
        }
        entry = create_log_entry("op", nested_data)

        assert entry.payload == nested_data


class TestImmutableLogPerformance:
    """性能相关测试"""

    def test_sha256_performance(self):
        """F01-T010: SHA256计算性能(基本验证)"""
        import time

        from f01_immutable_log.immutable_log import create_log_entry

        start = time.time()
        for i in range(100):
            create_log_entry("op", {"index": i, "data": "x" * 1000})
        elapsed = time.time() - start

        # 100次创建应该在1秒内完成
        assert elapsed < 1.0, f"SHA256 performance issue: {elapsed}s for 100 entries"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
