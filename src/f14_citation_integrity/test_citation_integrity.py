"""
F14: 引用完整性校验 - 单元测试
TDD RED阶段：测试必须失败，因为实现不存在
"""
import pytest
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Any
from datetime import datetime, timezone
from enum import Enum


class TestCitationRegistry:
    """引用注册表测试"""

    def test_register_citation(self):
        """F14-T001: 注册引用"""
        from f14_citation_integrity.citation_registry import CitationRegistry

        registry = CitationRegistry()

        citation_id = registry.register_citation(
            doi="10.1234/example",
            fact_hash="abc123",
            position={"page": 10, "line": 5}
        )

        assert citation_id is not None
        assert len(citation_id) > 0

    def test_register_duplicate_citation(self):
        """F14-T002: 注册重复引用"""
        from f14_citation_integrity.citation_registry import CitationRegistry

        registry = CitationRegistry()

        id1 = registry.register_citation(
            doi="10.1234/example",
            fact_hash="abc123",
            position={"page": 10}
        )

        id2 = registry.register_citation(
            doi="10.1234/example",
            fact_hash="abc123",
            position={"page": 10}
        )

        assert id1 == id2

    def test_get_citation(self):
        """F14-T003: 获取引用"""
        from f14_citation_integrity.citation_registry import CitationRegistry

        registry = CitationRegistry()

        registered_id = registry.register_citation(
            doi="10.1234/example",
            fact_hash="abc123",
            position={"page": 10}
        )

        citation = registry.get_citation(registered_id)

        assert citation is not None
        assert citation.doi == "10.1234/example"

    def test_get_nonexistent_citation(self):
        """F14-T004: 获取不存在的引用"""
        from f14_citation_integrity.citation_registry import CitationRegistry

        registry = CitationRegistry()

        citation = registry.get_citation("nonexistent-id")

        assert citation is None

    def test_list_citations_by_doi(self):
        """F14-T005: 按DOI列出引用"""
        from f14_citation_integrity.citation_registry import CitationRegistry

        registry = CitationRegistry()

        registry.register_citation(doi="10.1234/A", fact_hash="hash1", position={})
        registry.register_citation(doi="10.1234/B", fact_hash="hash2", position={})
        registry.register_citation(doi="10.1234/A", fact_hash="hash3", position={})

        citations = registry.list_citations_by_doi("10.1234/A")

        assert len(citations) == 2

    def test_citation_fact_tracking(self):
        """F14-T006: 引用事实追踪"""
        from f14_citation_integrity.citation_registry import CitationRegistry

        registry = CitationRegistry()

        registry.register_citation(doi="10.1234/example", fact_hash="hash1", position={})

        tracked = registry.get_fact_citations("hash1")

        assert len(tracked) == 1
        assert tracked[0].doi == "10.1234/example"

    def test_find_existing_citation_returns_none(self):
        """_find_existing_citation返回None (覆盖line 112)"""
        from f14_citation_integrity.citation_registry import CitationRegistry

        registry = CitationRegistry()

        registry.register_citation(doi="10.1234/test", fact_hash="hash1", position={"page": 1})

        result = registry._find_existing_citation("10.1234/test", "different_hash", {"page": 2})
        assert result is None

        result2 = registry._find_existing_citation("10.9999/nonexistent", "any_hash", {"page": 1})
        assert result2 is None


class TestCitationIntegrityManager:
    """引用完整性管理器测试"""

    def test_verify_citation_integrity(self):
        """F14-T007: 验证引用完整性"""
        from f14_citation_integrity.citation_integrity_manager import CitationIntegrityManager

        manager = CitationIntegrityManager()

        result = manager.verify_citation_integrity(
            doi="10.1234/example",
            fact_hash="abc123",
            content="测试内容"
        )

        assert result is not None
        assert hasattr(result, 'is_valid')

    def test_verify_citation_with_wrong_hash(self):
        """F14-T008: 验证错误哈希的引用"""
        from f14_citation_integrity.citation_integrity_manager import CitationIntegrityManager

        manager = CitationIntegrityManager()

        result = manager.verify_citation_integrity(
            doi="10.1234/example",
            fact_hash="wrong_hash",
            content="测试内容"
        )

        assert result.is_valid == False

    def test_detect_unverified_citations(self):
        """F14-T009: 检测未验证的引用"""
        from f14_citation_integrity.citation_integrity_manager import CitationIntegrityManager

        manager = CitationIntegrityManager()

        manager.register_unverified_citation("10.1234/A", "hash1")
        manager.register_unverified_citation("10.1234/B", "hash2")

        unverified = manager.get_unverified_citations()

        assert len(unverified) == 2

    def test_mark_citation_verified(self):
        """F14-T010: 标记引用已验证"""
        from f14_citation_integrity.citation_integrity_manager import CitationIntegrityManager

        manager = CitationIntegrityManager()

        manager.register_unverified_citation("10.1234/example", "hash1")

        manager.mark_citation_verified("10.1234/example", "hash1")

        unverified = manager.get_unverified_citations()
        assert len(unverified) == 0

    def test_citation_chain_validation(self):
        """F14-T011: 引用链验证"""
        from f14_citation_integrity.citation_integrity_manager import CitationIntegrityManager

        manager = CitationIntegrityManager()

        manager.register_unverified_citation("10.1234/A", "hash1")
        manager.register_unverified_citation("10.1234/B", "hash2")
        manager.register_unverified_citation("10.1234/C", "hash3")

        chain = manager.validate_citation_chain(["10.1234/A", "10.1234/B", "10.1234/C"])

        assert chain.is_valid == True

    def test_detect_fact_collision(self):
        """F14-T012: 检测事实冲突"""
        from f14_citation_integrity.citation_integrity_manager import CitationIntegrityManager

        manager = CitationIntegrityManager()

        manager.register_unverified_citation("10.1234/A", "hash1")
        manager.register_unverified_citation("10.1234/B", "hash1")

        collisions = manager.detect_fact_collision()

        assert len(collisions) >= 1


class TestSecurityTests:
    """安全测试 - P0漏洞覆盖"""

    def test_fabricated_citation_rejection(self):
        """F14-S001: 捏造引用拒绝"""
        from f14_citation_integrity.citation_integrity_manager import CitationIntegrityManager

        manager = CitationIntegrityManager()

        result = manager.verify_citation_integrity(
            doi="10.FABRICATED/fake",
            fact_hash="fakehash",
            content="捏造内容"
        )

        assert result.is_valid == False

    def test_hash_collision_detection(self):
        """F14-S002: 哈希碰撞检测"""
        from f14_citation_integrity.citation_integrity_manager import CitationIntegrityManager

        manager = CitationIntegrityManager()

        content_a = "内容A"
        content_b = "内容B"
        hash_a = hashlib.sha256(content_a.encode()).hexdigest()
        hash_b = hashlib.sha256(content_b.encode()).hexdigest()

        result1 = manager.verify_citation_integrity(
            doi="10.1234/A",
            fact_hash=hash_a,
            content=content_a
        )

        result2 = manager.verify_citation_integrity(
            doi="10.1234/B",
            fact_hash=hash_b,
            content=content_b
        )

        assert result1.is_valid == True
        assert result2.is_valid == True

    def test_empty_doi_rejection(self):
        """F14-S003: 空DOI拒绝"""
        from f14_citation_integrity.citation_integrity_manager import CitationIntegrityManager

        manager = CitationIntegrityManager()

        result = manager.verify_citation_integrity(
            doi="",
            fact_hash="hash1",
            content="内容"
        )

        assert result.is_valid == False

    def test_nonexistent_doi_in_chain(self):
        """F14-S004: 链中不存在的DOI"""
        from f14_citation_integrity.citation_integrity_manager import CitationIntegrityManager

        manager = CitationIntegrityManager()

        chain = manager.validate_citation_chain(["10.1234/A", "10.DOES.NOT.EXIST"])

        assert chain.is_valid == False

    def test_self_referencing_citation(self):
        """F14-S005: 自我引用检测"""
        from f14_citation_integrity.citation_integrity_manager import CitationIntegrityManager

        manager = CitationIntegrityManager()

        manager.register_unverified_citation("10.1234/self", "hash_self")

        result = manager.validate_citation_chain(["10.1234/self"])

        assert result.is_biased == False

    def test_citation_integrity_tampering_detection(self):
        """F14-S006: 引用完整性篡改检测"""
        from f14_citation_integrity.citation_integrity_manager import CitationIntegrityManager

        manager = CitationIntegrityManager()

        original_content = "原始内容"
        original_hash = hashlib.sha256(original_content.encode()).hexdigest()

        result = manager.verify_citation_integrity(
            doi="10.1234/tampered",
            fact_hash=original_hash,
            content=original_content
        )

        assert result.is_valid == True

        tampered_result = manager.verify_citation_integrity(
            doi="10.1234/tampered",
            fact_hash=original_hash,
            content="被篡改的内容"
        )

        assert tampered_result.is_valid == False


class TestIntegrationTests:
    """集成测试"""

    def test_full_citation_workflow(self):
        """F14-I001: 完整引用工作流"""
        from f14_citation_integrity.citation_integrity_manager import CitationIntegrityManager
        from f14_citation_integrity.citation_registry import CitationRegistry

        registry = CitationRegistry()
        manager = CitationIntegrityManager()

        content = "测试内容"
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        citation_id = registry.register_citation(
            doi="10.1234/fulltest",
            fact_hash=content_hash,
            position={"page": 1}
        )

        result = manager.verify_citation_integrity(
            doi="10.1234/fulltest",
            fact_hash=content_hash,
            content=content
        )

        assert result.is_valid == True

    def test_registry_and_manager_integration(self):
        """F14-I002: 注册表和管理器集成"""
        from f14_citation_integrity.citation_integrity_manager import CitationIntegrityManager

        manager = CitationIntegrityManager()

        manager.register_unverified_citation("10.1234/A", "hash_A")
        manager.register_unverified_citation("10.1234/B", "hash_B")

        unverified = manager.get_unverified_citations()

        assert len(unverified) == 2

        manager.mark_citation_verified("10.1234/A", "hash_A")

        unverified_after = manager.get_unverified_citations()
        assert len(unverified_after) == 1


class TestCitationIntegrityUncovered:
    """覆盖CitationIntegrityManager未测试的分支"""

    def test_mark_citation_verified_not_found(self):
        """mark_citation_verified处理不存在的引用 (覆盖line 124)"""
        from f14_citation_integrity.citation_integrity_manager import CitationIntegrityManager

        manager = CitationIntegrityManager()
        result = manager.mark_citation_verified("10.9999/nonexistent", "nonexistent_hash")
        assert result == False

    def test_validate_citation_chain_invalid_format(self):
        """validate_citation_chain处理无效DOI格式 (覆盖line 132)"""
        from f14_citation_integrity.citation_integrity_manager import CitationIntegrityManager

        manager = CitationIntegrityManager()
        result = manager.validate_citation_chain(["invalid-doi", "10.1234/valid"])

        assert len(result.issues) > 0
        assert any("Invalid DOI" in issue for issue in result.issues)

    def test_validate_citation_chain_self_reference(self):
        """validate_citation_chain检测自引用 (覆盖line 136)"""
        from f14_citation_integrity.citation_integrity_manager import CitationIntegrityManager

        manager = CitationIntegrityManager()
        result = manager.validate_citation_chain(["10.1234/A", "10.1234/A"])

        assert len(result.issues) > 0
        assert any("Self-referencing" in issue for issue in result.issues)

    def test_get_citation_statistics(self):
        """get_citation_statistics返回统计信息 (覆盖lines 175-184)"""
        from f14_citation_integrity.citation_integrity_manager import CitationIntegrityManager

        manager = CitationIntegrityManager()
        manager.register_unverified_citation("10.1234/A", "hash_A")
        manager.register_unverified_citation("10.1234/B", "hash_B")

        stats = manager.get_citation_statistics()

        assert stats["total_citations"] == 2
        assert stats["unverified_citations"] == 2
        assert stats["verification_rate"] == 0.0

    def test_is_valid_doi_format_empty(self):
        """_is_valid_doi_format处理空字符串 (覆盖lines 188-189)"""
        from f14_citation_integrity.citation_integrity_manager import CitationIntegrityManager

        manager = CitationIntegrityManager()
        result = manager._is_valid_doi_format("")
        assert result == False

    def test_registry_property(self):
        """registry属性返回注册表 (覆盖line 195)"""
        from f14_citation_integrity.citation_integrity_manager import CitationIntegrityManager

        manager = CitationIntegrityManager()
        assert manager.registry is not None
