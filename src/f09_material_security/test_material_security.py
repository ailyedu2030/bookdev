"""
F09: 素材安全管理 - 单元测试
TDD RED阶段：测试必须失败，因为实现不存在
"""

import pytest


class TestMaterialSecurity:
    """素材安全管理 - TDD RED阶段"""

    @pytest.mark.asyncio
    async def test_material_must_have_source(self):
        """F09-T001: 素材必须有来源"""
        from f09_material_security.material_security_manager import (
            Material,
            MaterialSecurityManager,
            MaterialValidationError,
        )

        manager = MaterialSecurityManager()

        material = Material(
            content="测试内容",
            source=None
        )

        with pytest.raises(MaterialValidationError):
            await manager.register_material(material)

    @pytest.mark.asyncio
    async def test_trust_score_calculation(self):
        """F09-T002: 可信度评分计算"""
        from f09_material_security.material_security_manager import Material, MaterialSecurityManager, SourceInfo

        manager = MaterialSecurityManager()

        material = Material(
            content="权威机构发布的内容",
            source=SourceInfo(
                name="国家统计局",
                trust_level="WHITELIST"
            )
        )

        score = manager.calculate_trust_score(material)
        assert score >= 0.9

    @pytest.mark.asyncio
    async def test_low_trust_material_blocked(self):
        """F09-T003: 低可信度素材被阻断"""
        from f09_material_security.material_security_manager import Material, MaterialSecurityManager, SourceInfo

        manager = MaterialSecurityManager()

        material = Material(
            content="未核实的内容",
            source=SourceInfo(
                name="未知来源",
                trust_level="UNKNOWN"
            )
        )

        result = await manager.register_material(material)
        assert result.status == "REJECTED"
        assert result.trust_score < 0.7

    @pytest.mark.asyncio
    async def test_whitelisted_source_auto_approved(self):
        """F09-T004: 白名单来源自动批准"""
        from f09_material_security.material_security_manager import Material, MaterialSecurityManager, SourceInfo

        manager = MaterialSecurityManager()

        material = Material(
            content="官方政策内容",
            source=SourceInfo(
                name="教育部",
                trust_level="WHITELIST"
            )
        )

        result = await manager.register_material(material)
        assert result.status == "APPROVED"

    @pytest.mark.asyncio
    async def test_security_scan_detects_sensitive_content(self):
        """F09-T005: 安全扫描检测敏感内容"""
        from f09_material_security.material_security_manager import MaterialSecurityManager, ScanStatus

        manager = MaterialSecurityManager()

        result = await manager.security_scan(
            "包含恶意内容"
        )

        assert result.sensitive_word_count > 0
        assert result.scan_status in [ScanStatus.WARNING, ScanStatus.BLOCKED]

    @pytest.mark.asyncio
    async def test_retrieval_weight_degradation(self):
        """F09-T006: 检索权重降权"""
        from f09_material_security.material_security_manager import MaterialSecurityManager

        manager = MaterialSecurityManager()

        weight = manager.get_retrieval_weight("material-001")
        assert weight < 1.0


class TestSourceRegistry:
    """素材来源注册表测试"""

    @pytest.mark.asyncio
    async def test_register_source(self):
        """F09-T007: 注册来源"""
        from f09_material_security.source_registry import MaterialSourceRegistry, SourceInfo

        registry = MaterialSourceRegistry()

        source = SourceInfo(
            name="新来源",
            trust_level="VERIFIED"
        )

        result = await registry.register_source(source)
        assert result.registered is True

    @pytest.mark.asyncio
    async def test_register_duplicate_source_rejected(self):
        """F09-T007b: 重复注册来源被拒绝 (covers line 48)"""
        from f09_material_security.source_registry import MaterialSourceRegistry, SourceInfo

        registry = MaterialSourceRegistry()

        source = SourceInfo(name="唯一来源", trust_level="VERIFIED")
        result1 = await registry.register_source(source)
        assert result1.registered is True

        result2 = await registry.register_source(source)
        assert result2.registered is False
        assert "already registered" in result2.reason

    @pytest.mark.asyncio
    async def test_is_whitelisted(self):
        """F09-T008: 检查是否在白名单"""
        from f09_material_security.source_registry import MaterialSourceRegistry

        registry = MaterialSourceRegistry()

        assert registry.is_whitelisted("国家统计局") is True
        assert registry.is_whitelisted("未知来源") is False

    @pytest.mark.asyncio
    async def test_is_whitelisted_registered_source(self):
        """F09-T008b: 已注册来源白名单检查 (covers line 71)"""
        from f09_material_security.source_registry import MaterialSourceRegistry, SourceInfo

        registry = MaterialSourceRegistry()

        # Register a source with WHITELIST trust_level
        whitelisted = SourceInfo(name="某认证机构", trust_level="WHITELIST")
        await registry.register_source(whitelisted)

        # Register a source with non-WHITELIST trust_level
        unknown = SourceInfo(name="普通来源", trust_level="UNKNOWN")
        await registry.register_source(unknown)

        assert registry.is_whitelisted("某认证机构") is True
        assert registry.is_whitelisted("普通来源") is False

    @pytest.mark.asyncio
    async def test_verify_whitelisted_source(self):
        """F09-T008c: 核实白名单来源通过 (covers lines 61-63)"""
        from f09_material_security.source_registry import MaterialSourceRegistry, SourceInfo

        registry = MaterialSourceRegistry()
        source = SourceInfo(name="认证来源", trust_level="WHITELIST")
        await registry.register_source(source)

        assert await registry.verify_source("认证来源") is True

    @pytest.mark.asyncio
    async def test_verify_verified_source(self):
        """F09-T008d: 核实已验证来源通过 (covers lines 61-63)"""
        from f09_material_security.source_registry import MaterialSourceRegistry, SourceInfo

        registry = MaterialSourceRegistry()
        source = SourceInfo(name="已验证来源", trust_level="VERIFIED")
        await registry.register_source(source)

        assert await registry.verify_source("已验证来源") is True

    @pytest.mark.asyncio
    async def test_verify_untrusted_source_fails(self):
        """F09-T008e: 核实未信任来源失败 (covers line 64)"""
        from f09_material_security.source_registry import MaterialSourceRegistry, SourceInfo

        registry = MaterialSourceRegistry()
        source = SourceInfo(name="未知来源", trust_level="UNKNOWN")
        await registry.register_source(source)

        assert await registry.verify_source("未知来源") is False

    @pytest.mark.asyncio
    async def test_verify_nonexistent_source_fails(self):
        """F09-T008f: 核实不存在的来源失败 (covers line 64)"""
        from f09_material_security.source_registry import MaterialSourceRegistry

        registry = MaterialSourceRegistry()
        assert await registry.verify_source("不存在的来源") is False

    @pytest.mark.asyncio
    async def test_get_source_info_registered(self):
        """F09-T008g: 获取已注册来源信息 (covers lines 76-77)"""
        from f09_material_security.source_registry import MaterialSourceRegistry, SourceInfo

        registry = MaterialSourceRegistry()
        source = SourceInfo(name="测试来源", url="https://test.com", trust_level="VERIFIED")
        await registry.register_source(source)

        info = registry.get_source_info("测试来源")
        assert info is not None
        assert info.name == "测试来源"
        assert info.url == "https://test.com"
        assert info.trust_level == "VERIFIED"

    @pytest.mark.asyncio
    async def test_get_source_info_whitelist_fallback(self):
        """F09-T008h: 获取白名单内置来源信息 (covers lines 78-82)"""
        from f09_material_security.source_registry import MaterialSourceRegistry

        registry = MaterialSourceRegistry()

        info = registry.get_source_info("教育部")
        assert info is not None
        assert info.name == "教育部"
        assert info.trust_level == "WHITELIST"

    @pytest.mark.asyncio
    async def test_get_source_info_not_found(self):
        """F09-T008i: 获取不存在的来源返回None (covers line 83)"""
        from f09_material_security.source_registry import MaterialSourceRegistry

        registry = MaterialSourceRegistry()
        assert registry.get_source_info("不存在的来源") is None

    def test_get_all_sources(self):
        """F09-T008j: 获取所有注册来源 (covers line 87)"""
        from f09_material_security.source_registry import MaterialSourceRegistry, SourceInfo

        registry = MaterialSourceRegistry()
        assert len(registry.get_all_sources()) == 0

        registry._registered_sources["A"] = SourceInfo(name="A")
        registry._registered_sources["B"] = SourceInfo(name="B")
        assert len(registry.get_all_sources()) == 2

    @pytest.mark.asyncio
    async def test_source_trust_levels(self):
        """F09-T009: 来源可信度等级"""
        from f09_material_security.material_security_manager import SourceInfo

        levels = ["WHITELIST", "VERIFIED", "UNKNOWN", "UNTRUSTED"]

        for level in levels:
            source = SourceInfo(name="测试", trust_level=level)
            assert source.trust_level == level


class TestSecurityTests:
    """安全测试 - P0漏洞覆盖"""

    @pytest.mark.asyncio
    async def test_malicious_material_detection(self):
        """F09-S001: 恶意素材检测 - P0-4漏洞防御"""
        from f09_material_security.material_security_manager import MaterialSecurityManager, ScanStatus

        manager = MaterialSecurityManager()

        result = await manager.security_scan(
            "恶意内容包含可疑链接 http://malicious.com"
        )

        assert result.scan_status == ScanStatus.BLOCKED

    @pytest.mark.asyncio
    async def test_tampering_detection(self):
        """F09-S002: 篡改检测"""
        from f09_material_security.material_security_manager import MaterialSecurityManager

        manager = MaterialSecurityManager()

        original_content = "原始内容"
        tampered_content = "被篡改的内容"

        result = manager.detect_tampering(original_content, tampered_content)
        assert result["tampering_detected"] is True

    @pytest.mark.asyncio
    async def test_whitelist_trust_boost(self):
        """F09-S003: 白名单来源信任度提升"""
        from f09_material_security.material_security_manager import Material, MaterialSecurityManager, SourceInfo

        manager = MaterialSecurityManager()

        material = Material(
            content="政府发布内容",
            source=SourceInfo(name="国务院", trust_level="WHITELIST")
        )

        score = manager.calculate_trust_score(material)
        assert score == 1.0

    @pytest.mark.asyncio
    async def test_untrusted_source_penalty(self):
        """F09-S004: 不可信来源惩罚"""
        from f09_material_security.material_security_manager import Material, MaterialSecurityManager, SourceInfo

        manager = MaterialSecurityManager()

        material = Material(
            content="可疑内容",
            source=SourceInfo(name="可疑网站", trust_level="UNTRUSTED")
        )

        score = manager.calculate_trust_score(material)
        assert score < 0.3


class TestIntegrationTests:
    """集成测试 - 模块间交互"""

    @pytest.mark.asyncio
    async def test_full_registration_workflow(self):
        """F09-I001: 完整注册工作流"""
        from f09_material_security.material_security_manager import Material, MaterialSecurityManager, SourceInfo

        manager = MaterialSecurityManager()

        material = Material(
            content="权威机构发布的内容",
            source=SourceInfo(name="国家统计局", trust_level="WHITELIST")
        )

        result = await manager.register_material(material)
        assert result.status == "APPROVED"
        assert result.trust_score >= 0.9

    @pytest.mark.asyncio
    async def test_manager_and_registry_integration(self):
        """F09-I002: 管理器与注册表集成"""
        from f09_material_security.material_security_manager import MaterialSecurityManager
        from f09_material_security.source_registry import MaterialSourceRegistry

        registry = MaterialSourceRegistry()
        manager = MaterialSecurityManager(source_registry=registry)

        weight = manager.get_retrieval_weight("unknown-material")
        assert weight < 1.0


class TestMaterialSecurityUncoveredBranches:
    """覆盖MaterialSecurityManager未测试的分支"""

    @pytest.mark.asyncio
    async def test_register_duplicate_material(self):
        """register_material处理重复注册 (覆盖lines 108-110)"""
        from f09_material_security.material_security_manager import Material, MaterialSecurityManager, SourceInfo

        manager = MaterialSecurityManager()

        material = Material(
            material_id="duplicate-id",
            content="Test content",
            source=SourceInfo(name="Test", trust_level="VERIFIED")
        )

        await manager.register_material(material)
        result2 = await manager.register_material(material)

        assert result2.status == "REJECTED"
        assert "already registered" in result2.reason

    @pytest.mark.asyncio
    async def test_register_material_blocked_by_scan(self):
        """register_material处理扫描阻断 (覆盖line 121)"""
        from f09_material_security.material_security_manager import Material, MaterialSecurityManager, SourceInfo

        manager = MaterialSecurityManager()

        material = Material(
            content="Visit https://malicious-site.com for more info",
            source=SourceInfo(name="Test", trust_level="VERIFIED")
        )

        result = await manager.register_material(material)
        assert result.status == "REJECTED"

    def test_calculate_trust_score_no_source(self):
        """calculate_trust_score处理无来源 (覆盖lines 189-190)"""
        from f09_material_security.material_security_manager import Material, MaterialSecurityManager

        manager = MaterialSecurityManager()

        material = Material(content="Content without source")
        material.source = None

        score = manager.calculate_trust_score(material)
        assert score == 0.0

    def test_get_retrieval_weight_cached(self):
        """get_retrieval_weight返回缓存权重 (覆盖lines 200-201)"""
        from f09_material_security.material_security_manager import Material, MaterialSecurityManager, SourceInfo

        manager = MaterialSecurityManager()

        Material(
            material_id="cached-material",
            content="Test content",
            source=SourceInfo(name="Test", trust_level="VERIFIED")
        )

        manager._material_weights["cached-material"] = 0.5

        weight = manager.get_retrieval_weight("cached-material")
        assert weight == 0.5

    def test_get_retrieval_weight_fallback(self):
        """get_retrieval_weight返回默认权重 (覆盖line 209)"""
        from f09_material_security.material_security_manager import MaterialSecurityManager

        manager = MaterialSecurityManager()

        weight = manager.get_retrieval_weight("completely-nonexistent-id")
        assert weight == 0.3

    @pytest.mark.asyncio
    async def test_register_material_unknown_trust_status_pending(self):
        """register_material处理UNKNOWN trust_level且trust_score>=阈值时status=PENDING (覆盖line 141)"""
        from f09_material_security.material_security_manager import (
            Material,
            MaterialSecurityManager,
            SourceInfo,
        )

        class TestableManager(MaterialSecurityManager):
            BLOCK_THRESHOLDS = {"min_trust_score": 0.3, "min_scan_score": 0.9}

        manager = TestableManager()

        material = Material(
            content="无敏感词的未知来源内容",
            source=SourceInfo(name="未知机构", trust_level="UNKNOWN")
        )

        result = await manager.register_material(material)
        assert result.status == "PENDING"
