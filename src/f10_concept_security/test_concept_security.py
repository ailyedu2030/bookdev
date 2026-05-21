"""
F10: 概念节点安全 - 单元测试
TDD RED阶段：测试必须失败，因为实现不存在
"""
import hashlib

import pytest


class TestConceptNodeSecurity:
    """概念节点安全 - TDD RED阶段"""

    def test_concept_node_requires_source_chunk(self):
        """F10-T001: 概念节点必须有来源chunk"""
        from f10_concept_security.concept_security import ConceptValidationError, KnowledgeGraphSecurity

        kg_security = KnowledgeGraphSecurity()

        with pytest.raises(ConceptValidationError):
            kg_security.create_concept_node(
                definition="人工智能是...", source_chunk_id=None, model_id="claude-3-5-sonnet"
            )

    def test_concept_node_requires_approved_model(self):
        """F10-T002: 概念节点必须使用白名单模型"""
        from f10_concept_security.concept_security import KnowledgeGraphSecurity, SecurityException

        kg_security = KnowledgeGraphSecurity()

        with pytest.raises(SecurityException):
            kg_security.create_concept_node(
                definition="人工智能是...", source_chunk_id="chunk-001", model_id="unapproved-model"
            )

    def test_integrity_verification_via_hash(self):
        """F10-T003: 通过哈希验证完整性"""
        from f10_concept_security.concept_security import KnowledgeGraphSecurity

        kg_security = KnowledgeGraphSecurity()

        node = kg_security.create_concept_node(
            definition="人工智能是研究、开发用于模拟、延伸和扩展人的智能的理论、方法、技术及应用系统。",
            source_chunk_id="chunk-001",
            model_id="claude-3-5-sonnet",
        )

        result = kg_security.verify_integrity(node)
        assert result.is_integral is True

    def test_tampering_detection(self):
        """F10-T004: 篡改检测"""
        from f10_concept_security.concept_security import KnowledgeGraphSecurity

        kg_security = KnowledgeGraphSecurity()

        node = kg_security.create_concept_node(
            definition="人工智能是...", source_chunk_id="chunk-001", model_id="claude-3-5-sonnet"
        )

        node.definition = "被篡改的定义"

        result = kg_security.verify_integrity(node)
        assert result.tampering_detected is True

    def test_confidence_based_review_decision(self):
        """F10-T005: 基于置信度的审核决策"""
        from f10_concept_security.concept_security import ConceptNode

        high_confidence_node = ConceptNode(
            concept_id="c-001",
            definition="清晰定义",
            confidence=0.98,
            source_chunk_id="chunk-001",
            model_id="claude-3-5-sonnet",
        )
        assert high_confidence_node.should_auto_approve is True

        medium_confidence_node = ConceptNode(
            concept_id="c-002",
            definition="较清晰定义",
            confidence=0.85,
            source_chunk_id="chunk-002",
            model_id="claude-3-5-sonnet",
        )
        assert medium_confidence_node.requires_manual_review is True

    def test_review_signature_required(self):
        """F10-T006: 审核需要签名"""
        from f10_concept_security.concept_security import KnowledgeGraphSecurity, SecurityException

        kg_security = KnowledgeGraphSecurity()

        with pytest.raises(SecurityException):
            kg_security.verify_and_approve(concept_id="c-001", reviewer_id=None)


class TestIntegrityVerifier:
    """完整性验证器测试"""

    def test_verify_hash_matches(self):
        """F10-T007: 验证哈希匹配"""
        from f10_concept_security.integrity_verifier import IntegrityVerifier

        verifier = IntegrityVerifier()

        content = "测试内容"
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        result = verifier.verify_hash(content, content_hash)
        assert result.is_valid is True

    def test_verify_hash_mismatch(self):
        """F10-T008: 验证哈希不匹配"""
        from f10_concept_security.integrity_verifier import IntegrityVerifier

        verifier = IntegrityVerifier()

        result = verifier.verify_hash("原始内容", "错误的哈希")
        assert result.is_valid is False

    def test_source_chunk_verification(self):
        """F10-T009: 验证源chunk存在"""
        from f10_concept_security.integrity_verifier import IntegrityVerifier

        verifier = IntegrityVerifier()

        result = verifier.verify_source_chunk_exists("chunk-001")
        assert result.exists is True


class TestSecurityTests:
    """安全测试 - P0漏洞覆盖"""

    def test_malicious_concept_detection(self):
        """F10-S001: 恶意概念检测 - P0-5漏洞防御"""
        from f10_concept_security.concept_security import KnowledgeGraphSecurity, SecurityException

        kg_security = KnowledgeGraphSecurity()

        with pytest.raises(SecurityException):
            kg_security.create_concept_node(
                definition="恶意概念定义", source_chunk_id="chunk-001", model_id="unapproved-model"
            )

    def test_untrained_model_rejection(self):
        """F10-S002: 未训练模型拒绝"""
        from f10_concept_security.concept_security import KnowledgeGraphSecurity, SecurityException

        kg_security = KnowledgeGraphSecurity()

        with pytest.raises(SecurityException):
            kg_security.create_concept_node(
                definition="测试定义", source_chunk_id="chunk-001", model_id="unknown-model"
            )

    def test_confidence_threshold_enforcement(self):
        """F10-S003: 置信度阈值执行"""
        from f10_concept_security.concept_security import KnowledgeGraphSecurity

        kg_security = KnowledgeGraphSecurity()

        node = kg_security.create_concept_node(
            definition="低质量定义", source_chunk_id="chunk-001", model_id="claude-3-5-sonnet", confidence=0.5
        )

        assert node.status == "REJECTED"


class TestIntegrationTests:
    """集成测试 - 模块间交互"""

    def test_full_concept_creation_workflow(self):
        """F10-I001: 完整概念创建工作流"""
        from f10_concept_security.concept_security import KnowledgeGraphSecurity

        kg_security = KnowledgeGraphSecurity()

        node = kg_security.create_concept_node(
            definition="人工智能是研究、开发用于模拟、延伸和扩展人的智能的理论、方法、技术及应用系统。",
            source_chunk_id="chunk-001",
            model_id="claude-3-5-sonnet",
        )

        assert node.concept_id is not None
        assert node.definition_hash is not None

        integrity_result = kg_security.verify_integrity(node)
        assert integrity_result.is_integral is True

    def test_security_and_integrity_integration(self):
        """F10-I002: 安全与完整性集成"""
        from f10_concept_security.concept_security import KnowledgeGraphSecurity

        kg_security = KnowledgeGraphSecurity()

        node = kg_security.create_concept_node(
            definition="有效定义", source_chunk_id="chunk-001", model_id="claude-3-5-sonnet"
        )

        assert kg_security.verify_integrity(node).is_integral is True


class TestConceptSecurityUncovered:
    """覆盖ConceptSecurity未测试的分支"""

    def test_verify_and_approve_concept_not_found(self):
        """verify_and_approve处理不存在的概念 (覆盖lines 125-126)"""
        from f10_concept_security.concept_security import ConceptValidationError, KnowledgeGraphSecurity

        kg_security = KnowledgeGraphSecurity()

        with pytest.raises(ConceptValidationError, match="not found"):
            kg_security.verify_and_approve("nonexistent-id", "reviewer-001")

    def test_verify_source_chunk_cached(self):
        """verify_source_chunk_exists返回缓存结果 (覆盖line 36)"""
        from f10_concept_security.integrity_verifier import IntegrityVerifier

        verifier = IntegrityVerifier()

        result1 = verifier.verify_source_chunk_exists("chunk-001")
        assert result1.exists is True

        result2 = verifier.verify_source_chunk_exists("chunk-001")
        assert result2.exists is True
        assert result2.chunk_id == "chunk-001"

    def test_verify_and_approve_concept_success(self):
        """verify_and_approve成功批准概念 (覆盖lines 128-132)"""
        from f10_concept_security.concept_security import KnowledgeGraphSecurity

        kg_security = KnowledgeGraphSecurity()

        node = kg_security.create_concept_node(
            definition="有效定义", source_chunk_id="chunk-001", model_id="claude-3-5-sonnet"
        )

        result = kg_security.verify_and_approve(concept_id=node.concept_id, reviewer_id="reviewer-001")

        assert result["approved"] is True
        assert result["concept_id"] == node.concept_id
