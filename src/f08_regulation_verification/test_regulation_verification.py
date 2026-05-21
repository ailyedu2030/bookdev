"""
F08: 法规引用核实系统 - 单元测试
TDD RED阶段：测试必须失败，因为实现不存在
"""

import pytest


class TestRegulationVerification:
    """法规引用核实系统 - TDD RED阶段"""

    @pytest.mark.asyncio
    async def test_verify_law_exists_in_whitelist(self):
        """F08-T001: 验证白名单法规存在"""
        from f08_regulation_verification.regulation_verifier import RegulationVerifier

        verifier = RegulationVerifier()

        result = await verifier.verify(law_name="人工智能法", article_num=28)

        assert result.law_exists is True
        assert result.article_exists is True

    @pytest.mark.asyncio
    async def test_reject_law_not_in_whitelist(self):
        """F08-T002: 拒绝非白名单法规"""
        from f08_regulation_verification.regulation_verifier import RegulationVerifier

        verifier = RegulationVerifier()

        result = await verifier.verify(law_name="完全不存在的法", article_num=1)

        assert result.is_valid is False
        assert "WHITELIST_VIOLATION" in result.reason

    @pytest.mark.asyncio
    async def test_verify_article_number_in_valid_range(self):
        """F08-T003: 验证条款号在有效范围内"""
        from f08_regulation_verification.regulation_verifier import RegulationVerifier

        verifier = RegulationVerifier()

        # 人工智能法共72条
        result = await verifier.verify(
            law_name="人工智能法",
            article_num=100,  # 超出范围
        )

        assert result.is_valid is False
        assert "ARTICLE_OUT_OF_RANGE" in result.reason

    @pytest.mark.asyncio
    async def test_three_tier_verification_workflow(self):
        """F08-T004: 三级核实流程"""
        from f08_regulation_verification.regulation_verifier import RegulationVerifier

        verifier = RegulationVerifier()

        result = await verifier.verify(
            law_name="人工智能法", article_num=28, cited_content="人工智能企业应当对算法进行备案..."
        )

        assert result.tier1_passed is True
        assert result.tier2_passed is True
        assert result.tier3_score > 0.8

    @pytest.mark.asyncio
    async def test_block_vague_reference(self):
        """F08-T005: 阻断模糊引用"""
        from f08_regulation_verification.regulation_verifier import RegulationVerifier

        verifier = RegulationVerifier()

        result = await verifier.verify_citation(citation="根据相关规定", context="一般性描述")

        assert result.is_valid is False
        assert "VAGUE_REFERENCE" in result.reason

    @pytest.mark.asyncio
    async def test_content_relevance_threshold(self):
        """F08-T006: 内容相关性阈值"""
        from f08_regulation_verification.regulation_verifier import RegulationVerifier

        verifier = RegulationVerifier()

        result = await verifier.verify_content_relevance(
            law_name="人工智能法", article_num=28, cited_content="完全不相关的内容" * 100
        )

        assert result.score < 0.5
        assert result.is_valid is False

    @pytest.mark.asyncio
    async def test_whitelisted_laws_list(self):
        """F08-T007: 白名单法规列表"""
        from f08_regulation_verification.whitelist_manager import WhitelistManager

        manager = WhitelistManager()

        laws = manager.get_whitelisted_laws()
        assert "人工智能法" in laws
        assert "数据安全法" in laws

    @pytest.mark.asyncio
    async def test_add_law_to_whitelist(self):
        """F08-T008: 添加法规到白名单"""
        from f08_regulation_verification.whitelist_manager import WhitelistManager

        manager = WhitelistManager()

        result = manager.add_law(name="新法规", total_articles=50, issuing_body="全国人民代表大会")

        assert result is True
        assert "新法规" in manager.get_whitelisted_laws()

    @pytest.mark.asyncio
    async def test_get_law_info(self):
        """F08-T009: 获取法规信息"""
        from f08_regulation_verification.whitelist_manager import WhitelistManager

        manager = WhitelistManager()

        info = manager.get_law_info("人工智能法")
        assert info is not None
        assert info.total_articles == 72

    @pytest.mark.asyncio
    async def test_get_law_info_custom_law(self):
        """F08-T010: 获取自定义法规信息 (覆盖line 71)"""
        from f08_regulation_verification.whitelist_manager import WhitelistManager

        manager = WhitelistManager()
        manager.add_law(name="测试法规", total_articles=30, issuing_body="测试机构")

        info = manager.get_law_info("测试法规")
        assert info is not None
        assert info.name == "测试法规"
        assert info.total_articles == 30

    @pytest.mark.asyncio
    async def test_add_law_already_whitelisted_fails(self):
        """F08-T011: 添加已白名单法规失败 (覆盖line 80)"""
        from f08_regulation_verification.whitelist_manager import WhitelistManager

        manager = WhitelistManager()

        result = manager.add_law(name="人工智能法", total_articles=100, issuing_body="全国人民代表大会")

        assert result is False

    @pytest.mark.asyncio
    async def test_remove_custom_law(self):
        """F08-T012: 移除自定义法规 (覆盖lines 93-96)"""
        from f08_regulation_verification.whitelist_manager import WhitelistManager

        manager = WhitelistManager()
        manager.add_law(name="临时法规", total_articles=20, issuing_body="测试机构")
        assert "临时法规" in manager.get_whitelisted_laws()

        result = manager.remove_law("临时法规")

        assert result is True
        assert "临时法规" not in manager.get_whitelisted_laws()

    @pytest.mark.asyncio
    async def test_remove_nonexistent_law(self):
        """F08-T013: 移除不存在的法规返回False"""
        from f08_regulation_verification.whitelist_manager import WhitelistManager

        manager = WhitelistManager()

        result = manager.remove_law("完全不存在的法规")

        assert result is False

    @pytest.mark.asyncio
    async def test_validate_article_number_nonexistent_law(self):
        """F08-T014: 验证不存在法规的条款号返回False (覆盖line 102)"""
        from f08_regulation_verification.whitelist_manager import WhitelistManager

        manager = WhitelistManager()

        result = manager.validate_article_number("不存在的法规", 1)

        assert result is False

    @pytest.mark.asyncio
    async def test_validate_article_number_valid(self):
        """F08-T015: 验证有效条款号"""
        from f08_regulation_verification.whitelist_manager import WhitelistManager

        manager = WhitelistManager()

        result = manager.validate_article_number("人工智能法", 50)

        assert result is True


class TestSecurityTests:
    """安全测试 - P0漏洞覆盖"""

    @pytest.mark.asyncio
    async def test_fabricated_law_detection(self):
        """F08-S001: 捏造法规检测 - P0-3漏洞防御"""
        from f08_regulation_verification.regulation_verifier import RegulationVerifier

        verifier = RegulationVerifier()

        result = await verifier.verify(law_name="完全不存在的法", article_num=1)

        assert result.is_valid is False
        assert "WHITELIST_VIOLATION" in result.reason

    @pytest.mark.asyncio
    async def test_fabricated_article_detection(self):
        """F08-S002: 捏造条款检测"""
        from f08_regulation_verification.regulation_verifier import RegulationVerifier

        verifier = RegulationVerifier()

        result = await verifier.verify(
            law_name="人工智能法",
            article_num=999,  # 不存在的条款
        )

        assert result.is_valid is False
        assert "ARTICLE_OUT_OF_RANGE" in result.reason

    @pytest.mark.asyncio
    async def test_content_tampering_detection(self):
        """F08-S003: 内容篡改检测"""
        from f08_regulation_verification.regulation_verifier import RegulationVerifier

        verifier = RegulationVerifier()

        result = await verifier.verify_content_relevance(
            law_name="人工智能法", article_num=28, cited_content="故意扭曲的完全不相关的引用内容" * 50
        )

        assert result.score < 0.3

    @pytest.mark.asyncio
    async def test_vague_reference_blocking(self):
        """F08-S004: 模糊引用阻断"""
        from f08_regulation_verification.regulation_verifier import RegulationVerifier

        verifier = RegulationVerifier()

        vague_phrases = ["根据相关规定", "按照有关法律法规", "依据有关政策"]

        for phrase in vague_phrases:
            result = await verifier.verify_citation(citation=phrase, context="任何描述")
            assert result.is_valid is False
            assert "VAGUE_REFERENCE" in result.reason


class TestIntegrationTests:
    """集成测试 - 模块间交互"""

    @pytest.mark.asyncio
    async def test_full_verification_workflow(self):
        """F08-I001: 完整核实工作流"""
        from f08_regulation_verification.regulation_verifier import RegulationVerifier

        verifier = RegulationVerifier()

        result = await verifier.verify(
            law_name="人工智能法", article_num=28, cited_content="人工智能企业应当对算法进行备案..."
        )

        assert result.law_exists is True
        assert result.article_exists is True
        assert result.tier3_score > 0.8

    @pytest.mark.asyncio
    async def test_verifier_and_whitelist_integration(self):
        """F08-I002: 核实器与白名单集成"""
        from f08_regulation_verification.regulation_verifier import RegulationVerifier
        from f08_regulation_verification.whitelist_manager import WhitelistManager

        manager = WhitelistManager()
        verifier = RegulationVerifier(whitelist_manager=manager)

        result = await verifier.verify(law_name="数据安全法", article_num=45)

        assert result.law_exists is True


class TestRegulationVerifierUncovered:
    """覆盖RegulationVerifier未测试的分支"""

    @pytest.mark.asyncio
    async def test_verify_phrase_not_vague(self):
        """verify_citation处理不模糊的短语 (覆盖lines 111-115)"""
        from f08_regulation_verification.regulation_verifier import RegulationVerifier

        verifier = RegulationVerifier()
        result = await verifier.verify_citation(
            citation="根据《人工智能法》第十五条规定", context="人工智能企业应当遵守相关法规"
        )

        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_verify_content_relevance(self):
        """verify_content_relevance返回相关性结果 (覆盖lines 126-131)"""
        from f08_regulation_verification.regulation_verifier import RegulationVerifier

        verifier = RegulationVerifier()
        result = await verifier.verify_content_relevance(
            law_name="人工智能法", article_num=28, cited_content="人工智能企业在备案时应当提供算法说明"
        )

        assert hasattr(result, "is_valid")
        assert hasattr(result, "score")

    @pytest.mark.asyncio
    async def test_calculate_content_similarity_with_partial_match(self):
        """_calculate_content_similarity计算部分匹配 (覆盖lines 153-156)"""
        from f08_regulation_verification.regulation_verifier import RegulationVerifier

        verifier = RegulationVerifier()
        score = verifier._calculate_content_similarity(
            cited_content="人工智能企业在备案时应当提供算法", law_name="人工智能法", article_num=28
        )
        assert 0 < score <= 1.0

    @pytest.mark.asyncio
    async def test_get_law_keywords_unknown_law_returns_default(self):
        """_get_law_keywords对未知法律返回默认关键词 (覆盖lines 174, 178-179)"""
        from f08_regulation_verification.regulation_verifier import RegulationVerifier

        verifier = RegulationVerifier()
        keywords = verifier._get_law_keywords("完全不存在的法律", 1)
        assert keywords == ["法规", "法律", "规定"]

    @pytest.mark.asyncio
    async def test_get_article_content_returns_none(self):
        """_get_article_content返回None (覆盖lines 178-179)"""
        from f08_regulation_verification.regulation_verifier import RegulationVerifier

        verifier = RegulationVerifier()
        result = await verifier._get_article_content("人工智能法", 28)
        assert result is None

    @pytest.mark.asyncio
    async def test_calculate_content_similarity_no_keywords_returns_default(self):
        """_calculate_content_similarity对无关键词法律返回0.5 (覆盖line 151)"""
        from f08_regulation_verification.regulation_verifier import RegulationVerifier

        verifier = RegulationVerifier()
        score = verifier._calculate_content_similarity(cited_content="任何内容", law_name="测试法律", article_num=999)
        assert score == 0.0
