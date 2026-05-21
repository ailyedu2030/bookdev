"""
F07: DOI强制解析服务 - 单元测试
TDD RED阶段：测试必须失败，因为实现不存在
"""
import asyncio
from unittest.mock import AsyncMock, patch

import pytest


class TestDOIVerification:
    """DOI强制解析服务 - TDD RED阶段"""

    @pytest.mark.asyncio
    async def test_verify_valid_doi(self):
        """F07-T001: 验证有效DOI"""
        from f07_doi_verification.doi_verifier import DOIVerifier

        verifier = DOIVerifier()

        result = await verifier.verify("10.1234/example.123")

        assert result.exists is True
        assert result.metadata is not None

    @pytest.mark.asyncio
    async def test_reject_doi_without_prefix(self):
        """F07-T002: 拒绝无前缀DOI"""
        from f07_doi_verification.doi_verifier import DOIVerifier

        verifier = DOIVerifier()

        result = await verifier.verify("invalid-doi")

        assert result.exists is False
        assert "INVALID_FORMAT" in result.reason

    @pytest.mark.asyncio
    async def test_detect_nonexistent_doi(self):
        """F07-T003: 检测不存在的DOI"""
        from f07_doi_verification.doi_verifier import DOIVerifier

        verifier = DOIVerifier()

        result = await verifier.verify("10.9999/nonexistent")

        assert result.exists is False

    @pytest.mark.asyncio
    async def test_citation_must_include_fact_hash(self):
        """F07-T004: 引用必须包含fact_hash"""
        from f07_doi_verification.doi_verifier import Citation, CitationValidationError, DOIVerifier

        verifier = DOIVerifier()

        citation = Citation(
            doi="10.1234/example",
            fact_hash=None,  # 缺少fact_hash
        )

        with pytest.raises(CitationValidationError):
            verifier.validate_citation_format(citation)

    @pytest.mark.asyncio
    async def test_verify_citation_content_matches(self):
        """F07-T005: 验证引用内容与注册表一致"""
        from f07_doi_verification.doi_verifier import DOIVerifier, FactRegistry

        registry = FactRegistry()
        verifier = DOIVerifier(fact_registry=registry)

        content = "人工智能是研究、开发用于模拟、延伸和扩展人的智能的理论、方法、技术及应用系统..."
        fact_hash = registry.register_fact(content, ["10.1234/example"])

        result = await verifier.verify_citation_content(
            doi="10.1234/example", fact_hash=fact_hash, cited_content=content
        )

        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_circular_reference_detection(self):
        """F07-T006: 循环引用检测"""
        from f07_doi_verification.doi_verifier import Citation, DOIVerifier, FactRegistry

        registry = FactRegistry()
        verifier = DOIVerifier(fact_registry=registry)

        hash_a = registry.register_fact("事实A", ["doi-B"])
        hash_b = registry.register_fact("事实B", ["doi-A"])

        citations = [
            Citation(doi="doi-A", fact_hash=hash_a),
            Citation(doi="doi-B", fact_hash=hash_b),
        ]

        has_cycle = verifier.detect_circular_reference(citations)
        assert has_cycle is True

    @pytest.mark.asyncio
    async def test_doi_format_validation(self):
        """F07-T007: DOI格式验证"""
        from f07_doi_verification.doi_verifier import DOIVerifier

        verifier = DOIVerifier()

        valid_dois = [
            "10.1000/xyz123",
            "10.1234/example.123",
            "10.15959/journal.2024.001",
        ]

        for doi in valid_dois:
            assert verifier._is_valid_doi_format(doi) is True

        invalid_dois = [
            "invalid",
            "10.invalid",
            "xyz10.1234/test",
        ]

        for doi in invalid_dois:
            assert verifier._is_valid_doi_format(doi) is False

    @pytest.mark.asyncio
    async def test_crossref_api_called(self):
        """F07-T008: CrossRef API被正确调用"""
        from f07_doi_verification.crossref_client import CrossRefClient

        client = CrossRefClient()

        with patch.object(client, "fetch_doi_metadata", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {"DOI": "10.1234/example", "title": "Test Title", "author": "Test Author"}

            result = await client.fetch_doi_metadata("10.1234/example")
            mock_fetch.assert_called_once_with("10.1234/example")
            assert result["DOI"] == "10.1234/example"

    @pytest.mark.asyncio
    async def test_verify_doi_exists(self):
        """verify_doi_exists返回DOI是否存在 (覆盖lines 40-41)"""
        from f07_doi_verification.crossref_client import CrossRefClient

        client = CrossRefClient()

        with patch.object(client, "fetch_doi_metadata", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {"DOI": "10.1234/test"}
            exists = await client.verify_doi_exists("10.1234/test")
            assert exists is True

            mock_fetch.return_value = None
            exists = await client.verify_doi_exists("10.9999/nonexistent")
            assert exists is False


class TestFactRegistry:
    """事实注册表测试"""

    def test_register_fact(self):
        """F07-T009: 注册事实"""
        from f07_doi_verification.doi_verifier import FactRegistry

        registry = FactRegistry()

        content = "人工智能是研究、开发用于模拟、延伸和扩展人的智能..."
        fact_hash = registry.register_fact(content, ["10.1234/example"])

        assert fact_hash is not None
        assert len(fact_hash) == 64  # SHA-256 hash length

    def test_fact_hash_is_deterministic(self):
        """F07-T010: 相同内容产生相同的hash"""
        from f07_doi_verification.doi_verifier import FactRegistry

        registry = FactRegistry()

        content = "测试内容"
        hash1 = registry.register_fact(content, ["doi-A"])
        hash2 = registry.register_fact(content, ["doi-B"])

        assert hash1 == hash2

    def test_get_fact_history(self):
        """F07-T011: 获取事实历史"""
        from f07_doi_verification.doi_verifier import FactRegistry

        registry = FactRegistry()

        content = "原始内容"
        fact_hash = registry.register_fact(content, ["doi-A"])

        registry.add_version(fact_hash, "更新内容", "修正错误")

        history = registry.get_fact_history(fact_hash)
        assert len(history) == 2


class TestSecurityTests:
    """安全测试 - P0漏洞覆盖"""

    @pytest.mark.asyncio
    async def test_fabricated_doi_detection(self):
        """F07-S001: 捏造DOI检测 - P0-1漏洞防御"""
        from f07_doi_verification.doi_verifier import DOIVerifier

        verifier = DOIVerifier()

        # 明显捏造的DOI前缀
        result = await verifier.verify("10.99999/fabricated")

        assert result.exists is False

    @pytest.mark.asyncio
    async def test_citation_hash_tampering_detection(self):
        """F07-S002: 引用哈希篡改检测"""
        from f07_doi_verification.doi_verifier import DOIVerifier, FactRegistry

        registry = FactRegistry()
        verifier = DOIVerifier(fact_registry=registry)

        content = "原始内容"
        correct_hash = registry.register_fact(content, ["10.1234/example"])

        # 篡改内容
        tampered_content = "被篡改的内容"

        result = await verifier.verify_citation_content(
            doi="10.1234/example", fact_hash=correct_hash, cited_content=tampered_content
        )

        assert result.is_valid is False

    @pytest.mark.asyncio
    async def test_self_reference_cycle_detection(self):
        """F07-S003: 自我引用循环检测"""
        from f07_doi_verification.doi_verifier import Citation, DOIVerifier, FactRegistry

        registry = FactRegistry()
        verifier = DOIVerifier(fact_registry=registry)

        # A引用自己
        hash_a = registry.register_fact("事实A", ["doi-A"])

        citations = [
            Citation(doi="doi-A", fact_hash=hash_a),
        ]

        has_cycle = verifier.detect_circular_reference(citations)
        assert has_cycle is False  # 自己引用自己不算循环

        # A引用B，B引用A
        hash_a2 = registry.register_fact("事实A", ["doi-B"])
        hash_b = registry.register_fact("事实B", ["doi-A"])

        citations2 = [
            Citation(doi="doi-A", fact_hash=hash_a2),
            Citation(doi="doi-B", fact_hash=hash_b),
        ]

        has_cycle2 = verifier.detect_circular_reference(citations2)
        assert has_cycle2 is True

    @pytest.mark.asyncio
    async def test_long_chain_cycle_detection(self):
        """F07-S004: 长链循环检测"""
        from f07_doi_verification.doi_verifier import Citation, DOIVerifier, FactRegistry

        registry = FactRegistry()
        verifier = DOIVerifier(fact_registry=registry)

        # A -> B -> C -> D -> A (循环)
        # A被D引用，B被A引用，C被B引用，D被C引用
        hashes = []
        doi_refs = []
        for i in range(4):
            prev_doi = doi_refs[-1] if doi_refs else None
            doi_refs.append(f"doi-{chr(65+i)}")
            # A没有引用（作为起始），B引用A，C引用B，D引用C
            ref = [prev_doi] if prev_doi else []
            h = registry.register_fact(f"事实{chr(65+i)}", ref)
            hashes.append(h)

        # 修改A的source_refs使其引用D，形成循环
        fact_a = registry.get_fact(hashes[0])
        fact_a.source_refs = ["doi-D"]

        citations = [Citation(doi=f"doi-{chr(65+i)}", fact_hash=hashes[i]) for i in range(4)]

        has_cycle = verifier.detect_circular_reference(citations)
        assert has_cycle is True

    @pytest.mark.asyncio
    async def test_missing_fact_hash_rejection(self):
        """F07-S005: 缺少fact_hash的引用被拒绝"""
        from f07_doi_verification.doi_verifier import Citation, CitationValidationError, DOIVerifier

        verifier = DOIVerifier()

        citation = Citation(doi="10.1234/test", fact_hash="")

        with pytest.raises(CitationValidationError):
            verifier.validate_citation_format(citation)


class TestIntegrationTests:
    """集成测试 - 模块间交互"""

    @pytest.mark.asyncio
    async def test_full_doi_verification_workflow(self):
        """F07-I001: 完整DOI核实工作流"""
        from f07_doi_verification.doi_verifier import DOIVerifier, FactRegistry

        registry = FactRegistry()
        verifier = DOIVerifier(fact_registry=registry)

        # 1. 注册事实
        content = "人工智能是研究、开发用于模拟、延伸和扩展人的智能..."
        fact_hash = registry.register_fact(content, ["10.1234/ai-research"])

        # 2. 验证DOI存在
        doi_result = await verifier.verify("10.1234/ai-research")
        assert doi_result.exists is True

        # 3. 验证引用内容
        citation_result = await verifier.verify_citation_content(
            doi="10.1234/ai-research", fact_hash=fact_hash, cited_content=content
        )
        assert citation_result.is_valid is True

    @pytest.mark.asyncio
    async def test_verifier_and_registry_integration(self):
        """F07-I002: 核实器与注册表集成"""
        from f07_doi_verification.doi_verifier import Citation, DOIVerifier, FactRegistry

        registry = FactRegistry()
        verifier = DOIVerifier(fact_registry=registry)

        # 注册多个相关事实 - B引用A，无循环
        hash1 = registry.register_fact("事实A", [])
        hash2 = registry.register_fact("事实B", ["10.1234/A"])

        citations = [
            Citation(doi="10.1234/A", fact_hash=hash1),
            Citation(doi="10.1234/B", fact_hash=hash2),
        ]

        # 验证无循环引用
        has_cycle = verifier.detect_circular_reference(citations)
        assert has_cycle is False


class TestFactRegistryUncoveredBranches:
    """覆盖未测试的FactRegistry分支"""

    @pytest.mark.asyncio
    async def test_verify_fact_not_found(self):
        """verify_fact处理不存在的事实 (覆盖lines 83-84)"""
        from f07_doi_verification.doi_verifier import FactRegistry

        registry = FactRegistry()
        result = registry.verify_fact("nonexistent_hash", "verifier_001")

        assert result is False

    @pytest.mark.asyncio
    async def test_add_version_not_found(self):
        """add_version处理不存在的事实 (覆盖lines 93-94)"""
        from f07_doi_verification.doi_verifier import FactRegistry

        registry = FactRegistry()
        with pytest.raises(ValueError, match="not found"):
            registry.add_version("nonexistent_hash", "new content", "correction")

    @pytest.mark.asyncio
    async def test_verify_fact_success(self):
        """verify_fact成功验证 (覆盖lines 86-89)"""
        from f07_doi_verification.doi_verifier import FactRegistry

        registry = FactRegistry()
        hash1 = registry.register_fact("事实内容", [])

        result = registry.verify_fact(hash1, "verifier_001")

        assert result is True
        fact = registry._facts.get(hash1)
        assert fact is not None
        assert fact.is_verified is True
        assert fact.verifier_id == "verifier_001"

    def test_get_fact_history_not_found(self):
        """get_fact_history处理不存在的事实 (覆盖line 119)"""
        from f07_doi_verification.doi_verifier import FactRegistry

        registry = FactRegistry()
        result = registry.get_fact_history("nonexistent")
        assert result == []

    def test_get_fact_history_with_versions(self):
        """get_fact_history返回版本历史 (覆盖lines 122-131)"""
        from f07_doi_verification.doi_verifier import FactRegistry

        registry = FactRegistry()
        hash1 = registry.register_fact("原始内容", [])

        registry.add_version(hash1, "修改内容1", "第一次修改")
        registry.add_version(hash1, "修改内容2", "第二次修改")

        history = registry.get_fact_history(hash1)

        assert len(history) == 3
        assert history[0]["content"] == "原始内容"
        assert history[0]["version"] == 0
        assert history[2]["content"] == "修改内容2"
        assert history[2]["version"] == 2

    def test_fact_registry_property(self):
        """fact_registry属性返回注册表 (覆盖line 290)"""
        from f07_doi_verification.doi_verifier import DOIVerifier

        verifier = DOIVerifier()
        assert verifier.fact_registry is not None


class TestDOIVerifierUncovered:
    """覆盖DOIVerifier未测试的分支"""

    @pytest.mark.asyncio
    async def test_verify_timeout(self):
        """verify处理超时 (覆盖lines 176-182)"""
        from unittest.mock import AsyncMock, patch

        from f07_doi_verification.doi_verifier import DOIVerifier

        verifier = DOIVerifier()

        with patch.object(verifier, "_fetch_doi_metadata", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = TimeoutError()

            result = await verifier.verify("10.1234/test")

            assert result.exists is False
            assert "TIMEOUT" in result.reason

    @pytest.mark.asyncio
    async def test_verify_exception(self):
        """verify处理异常 (覆盖lines 183-189)"""
        from unittest.mock import AsyncMock, patch

        from f07_doi_verification.doi_verifier import DOIVerifier

        verifier = DOIVerifier()

        with patch.object(verifier, "_fetch_doi_metadata", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = Exception("Network error")

            result = await verifier.verify("10.1234/test")

            assert result.exists is False
            assert "ERROR:" in result.reason

    def test_is_valid_doi_format_empty(self):
        """_is_valid_doi_format处理空字符串 (覆盖line 194)"""
        from f07_doi_verification.doi_verifier import DOIVerifier

        verifier = DOIVerifier()
        result = verifier._is_valid_doi_format("")
        assert result is False


class TestCitationValidationUncovered:
    """覆盖CitationValidation未测试的分支"""

    def test_validate_citation_format_missing_fact_hash(self):
        """validate_citation_format处理缺失fact_hash (覆盖lines 211-213)"""
        from f07_doi_verification.doi_verifier import Citation, CitationValidationError, DOIVerifier

        verifier = DOIVerifier()
        citation = Citation(doi="10.1234/test", fact_hash=None)

        with pytest.raises(CitationValidationError, match="fact_hash"):
            verifier.validate_citation_format(citation)

    def test_validate_citation_format_missing_doi(self):
        """validate_citation_format处理缺失DOI (覆盖lines 215-216)"""
        from f07_doi_verification.doi_verifier import Citation, CitationValidationError, DOIVerifier

        verifier = DOIVerifier()
        citation = Citation(doi="", fact_hash="abc123")

        with pytest.raises(CitationValidationError, match="DOI"):
            verifier.validate_citation_format(citation)

    def test_validate_citation_format_invalid_format(self):
        """validate_citation_format处理无效DOI格式 (覆盖lines 218-221)"""
        from f07_doi_verification.doi_verifier import Citation, CitationValidationError, DOIVerifier

        verifier = DOIVerifier()
        citation = Citation(doi="invalid-format", fact_hash="abc123")

        with pytest.raises(CitationValidationError, match="Invalid DOI"):
            verifier.validate_citation_format(citation)
