"""
F03: 内容寻址哈希 - TDD RED阶段测试

按照TDD原则：
1. RED: 写失败测试
2. GREEN: 写最简实现让测试通过
3. Refactor: 优化代码质量
"""


import pytest


class TestContentAddressing:
    """内容寻址基础测试"""

    def test_content_hash_is_position_independent(self):
        """F03-T001: 内容哈希与位置无关"""
        from f03_content_addressing.content_addressing import calculate_content_hash

        hash1 = calculate_content_hash("Hello World", offset=0)
        hash2 = calculate_content_hash("Hello World", offset=100)
        assert hash1 == hash2

    def test_identical_content_produces_same_hash(self):
        """F03-T002: 相同内容产生相同哈希"""
        from f03_content_addressing.content_addressing import calculate_content_hash

        content1 = "人工智能是研究、开发用于模拟、延伸和扩展人的智能的理论、方法、技术..."
        content2 = "人工智能是研究、开发用于模拟、延伸和扩展人的智能的理论、方法、技术..."
        assert calculate_content_hash(content1) == calculate_content_hash(content2)

    def test_different_content_produces_different_hash(self):
        """F03-T003: 不同内容产生不同哈希"""
        from f03_content_addressing.content_addressing import calculate_content_hash

        hash1 = calculate_content_hash("内容A")
        hash2 = calculate_content_hash("内容B")
        assert hash1 != hash2

    def test_content_address_reference_format(self):
        """F03-T004: 引用格式正确"""
        from f03_content_addressing.content_addressing import ContentAddressReference

        ref = ContentAddressReference(
            content_hash="abc123",
            offset=0,
            length=500
        )

        assert ref.to_string() == "{hash: abc123, offset: 0, length: 500}"

    def test_auto_deduplication_via_hash(self):
        """F03-T005: 通过哈希自动去重"""
        from f03_content_addressing.content_addressing import deduplicate_by_hash

        contents = ["内容A", "内容B", "内容A", "内容C"]
        unique_hashes = deduplicate_by_hash(contents)
        assert len(unique_hashes) == 3

    def test_integrity_verification_success(self):
        """F03-T006: 完整性验证 - 成功"""
        from f03_content_addressing.content_addressing import calculate_content_hash, verify_integrity

        content = "原始内容"
        stored_hash = calculate_content_hash(content)

        assert verify_integrity(content, stored_hash) is True

    def test_integrity_verification_failure(self):
        """F03-T006b: 完整性验证 - 篡改检测"""
        from f03_content_addressing.content_addressing import calculate_content_hash, verify_integrity

        content = "原始内容"
        stored_hash = calculate_content_hash(content)

        tampered = "被篡改的内容"
        assert verify_integrity(tampered, stored_hash) is False


class TestContentAddressingHash:
    """内容哈希测试"""

    def test_hash_algorithm_is_sha256(self):
        """F03-T007: 使用SHA-256算法"""
        from f03_content_addressing.content_addressing import calculate_content_hash

        content = "test content"
        hash_result = calculate_content_hash(content)

        assert len(hash_result) == 64  # SHA-256 hex length

    def test_hash_is_hex_string(self):
        """F03-T007b: 哈希是十六进制字符串"""
        from f03_content_addressing.content_addressing import calculate_content_hash

        hash_result = calculate_content_hash("test")
        assert all(c in '0123456789abcdef' for c in hash_result)

    def test_hash_deterministic(self):
        """F03-T007c: 哈希是确定性的"""
        from f03_content_addressing.content_addressing import calculate_content_hash

        content = "deterministic content"
        for _ in range(10):
            assert calculate_content_hash(content) == calculate_content_hash(content)

    def test_empty_content_hash(self):
        """F03-T007d: 空内容哈希"""
        from f03_content_addressing.content_addressing import calculate_content_hash

        hash_result = calculate_content_hash("")
        assert len(hash_result) == 64

    def test_unicode_content_hash(self):
        """F03-T007e: Unicode内容哈希"""
        from f03_content_addressing.content_addressing import calculate_content_hash

        content = "人工智能 🧠"
        hash_result = calculate_content_hash(content)
        assert len(hash_result) == 64


class TestContentAddressReference:
    """内容地址引用测试"""

    def test_reference_equality_with_non_reference(self):
        """F03-T012: 与非ContentAddressReference对象比较返回False"""
        from f03_content_addressing.content_addressing import ContentAddressReference

        ref = ContentAddressReference(content_hash="hash", offset=0, length=100)

        assert (ref == "not a reference") is False
        assert (ref == 42) is False
        assert (ref == {"content_hash": "hash", "offset": 0, "length": 100}) is False

    def test_reference_creation(self):
        """F03-T008: 创建引用"""
        from f03_content_addressing.content_addressing import ContentAddressReference

        ref = ContentAddressReference(
            content_hash="hash123",
            offset=10,
            length=100
        )

        assert ref.content_hash == "hash123"
        assert ref.offset == 10
        assert ref.length == 100

    def test_reference_from_content(self):
        """F03-T008b: 从内容创建引用"""
        from f03_content_addressing.content_addressing import calculate_content_hash, create_reference_from_content

        content = "测试内容段落"
        ref = create_reference_from_content(content)

        assert ref.content_hash == calculate_content_hash(content)
        assert ref.length == len(content)

    def test_reference_equality(self):
        """F03-T008c: 引用相等"""
        from f03_content_addressing.content_addressing import ContentAddressReference

        ref1 = ContentAddressReference(content_hash="hash", offset=0, length=100)
        ref2 = ContentAddressReference(content_hash="hash", offset=0, length=100)

        assert ref1 == ref2


class TestDeduplication:
    """去重测试"""

    def test_deduplicate_empty_list(self):
        """F03-T009: 空列表去重"""
        from f03_content_addressing.content_addressing import deduplicate_by_hash

        result = deduplicate_by_hash([])
        assert result == []

    def test_deduplicate_all_unique(self):
        """F03-T009b: 全是唯一内容"""
        from f03_content_addressing.content_addressing import deduplicate_by_hash

        contents = ["A", "B", "C"]
        result = deduplicate_by_hash(contents)
        assert len(result) == 3

    def test_deduplicate_all_same(self):
        """F03-T009c: 全是相同内容"""
        from f03_content_addressing.content_addressing import deduplicate_by_hash

        contents = ["相同", "相同", "相同"]
        result = deduplicate_by_hash(contents)
        assert len(result) == 1

    def test_deduplicate_preserves_first_occurrence(self):
        """F03-T009d: 保留首次出现"""
        from f03_content_addressing.content_addressing import deduplicate_by_hash

        contents = ["first", "second", "first", "third"]
        result = deduplicate_by_hash(contents)
        assert result == ["first", "second", "third"]


class TestContentAddressingEdgeCases:
    """边界条件测试"""

    def test_very_long_content(self):
        """F03-T010: 极长内容"""
        from f03_content_addressing.content_addressing import calculate_content_hash

        long_content = "x" * 1_000_000
        hash_result = calculate_content_hash(long_content)
        assert len(hash_result) == 64

    def test_special_characters(self):
        """F03-T010b: 特殊字符"""
        from f03_content_addressing.content_addressing import calculate_content_hash

        special = '{"key": "value", "数组": [1, 2, 3]}'
        hash_result = calculate_content_hash(special)
        assert len(hash_result) == 64

    def test_newlines_and_tabs(self):
        """F03-T010c: 换行和制表符"""
        from f03_content_addressing.content_addressing import calculate_content_hash

        content = "line1\nline2\ttabbed"
        hash1 = calculate_content_hash(content)
        hash2 = calculate_content_hash("line1\nline2\ttabbed")
        assert hash1 == hash2


class TestContentAddressingWithOffset:
    """带偏移的哈希测试"""

    def test_offset_zero_hash(self):
        """F03-T011: offset=0应该正常计算"""
        from f03_content_addressing.content_addressing import calculate_content_hash

        hash1 = calculate_content_hash("content", offset=0)
        hash2 = calculate_content_hash("content")
        assert hash1 == hash2

    def test_offset_large_hash(self):
        """F03-T011b: 大偏移值"""
        from f03_content_addressing.content_addressing import calculate_content_hash

        hash1 = calculate_content_hash("content", offset=1000000)
        hash2 = calculate_content_hash("content")
        assert hash1 == hash2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
