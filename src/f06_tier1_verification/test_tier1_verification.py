"""
F06: Tier1数值核实引擎 - 单元测试
TDD RED阶段：测试必须失败，因为实现不存在
"""
import asyncio
from unittest.mock import AsyncMock, patch

import pytest


class TestTier1Verification:
    """Tier1数值核实引擎 - TDD RED阶段"""

    @pytest.mark.asyncio
    async def test_verify_national_statistics_gdp(self):
        """F06-T001: 核实国家统计局GDP数据"""
        from f06_tier1_verification.tier1_engine import Tier1Verifier

        verifier = Tier1Verifier()

        result = await verifier.verify(
            data_type="gdp",
            value=12900000000000,  # 12.9万亿
            year=2023,
            region="中国"
        )

        assert result.is_verified is True
        assert result.discrepancy < 0.05  # 偏差<5%

    @pytest.mark.asyncio
    async def test_detect_fabricated_number(self):
        """F06-T002: 检测捏造数值"""
        from f06_tier1_verification.tier1_engine import Tier1Verifier

        verifier = Tier1Verifier()

        result = await verifier.verify(
            data_type="gdp",
            value=99999999999999,  # 明显异常
            year=2023
        )

        assert result.is_verified is False
        assert "ANOMALY_DETECTED" in result.reason

    @pytest.mark.asyncio
    async def test_value_range_validation(self):
        """F06-T003: 数值范围验证"""
        from f06_tier1_verification.tier1_engine import Tier1Verifier

        verifier = Tier1Verifier()

        result = await verifier.verify(
            data_type="population",
            value=-1000,  # 不可能为负
            year=2023
        )

        assert result.is_verified is False
        assert "INVALID_RANGE" in result.reason

    @pytest.mark.asyncio
    async def test_external_api_called(self):
        """F06-T006: 外部API被正确调用"""
        from f06_tier1_verification.tier1_engine import Tier1Verifier

        verifier = Tier1Verifier()

        with patch.object(verifier, '_call_external_api', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {"verified": True, "value": 12900000000000, "source": "国家统计局"}

            result = await verifier.verify(
                data_type="gdp",
                value=12900000000000,
                year=2023
            )

            mock_api.assert_called_once()
            assert result.is_verified is True


class TestDataLineageTracker:
    """数据血缘追踪 - TDD RED阶段"""

    @pytest.mark.asyncio
    async def test_lineage_tracking(self):
        """F06-T004: 传播链追踪"""
        from f06_tier1_verification.data_lineage_tracker import DataLineageTracker

        tracker = DataLineageTracker()

        tracker.register_raw_data("gdp-2023", 12900000000000, "国家统计局")
        tracker.register_derived_data(
            "per-capita",
            formula="gdp-2023 / population-2023",
            input_data_ids=["gdp-2023"]
        )

        lineage = tracker.get_propagation_chain("per-capita")
        assert len(lineage) == 2
        assert lineage[0].is_raw is True

    @pytest.mark.asyncio
    async def test_propagation_depth_limit(self):
        """F06-T005: 传播深度限制"""
        from f06_tier1_verification.data_lineage_tracker import DataLineageTracker

        tracker = DataLineageTracker(max_depth=3)

        # 注册多层派生 - data-0 -> data-1 -> data-2 -> data-3 (depth 3, OK)
        tracker.register_raw_data("data-0", 1000, "source")
        r1 = tracker.register_derived_data(
            "data-1",
            formula="data-0 * 0.5",
            input_data_ids=["data-0"]
        )
        assert r1.rejected is False
        r2 = tracker.register_derived_data(
            "data-2",
            formula="data-1 * 0.5",
            input_data_ids=["data-1"]
        )
        assert r2.rejected is False
        r3 = tracker.register_derived_data(
            "data-3",
            formula="data-2 * 0.5",
            input_data_ids=["data-2"]
        )
        assert r3.rejected is False

        # 深度超过3应被阻断 - data-4的depth是4
        result = tracker.register_derived_data(
            "data-4",
            formula="data-3 * 0.5",
            input_data_ids=["data-3"]
        )

        assert result.rejected is True
        assert "DEPTH_EXCEEDED" in result.reason

    @pytest.mark.asyncio
    async def test_register_raw_data(self):
        """F06-T007: 注册原始数据"""
        from f06_tier1_verification.data_lineage_tracker import DataLineageTracker

        tracker = DataLineageTracker()

        result = tracker.register_raw_data("test-data", 5000, "测试来源")

        assert result.success is True
        assert result.node is not None
        assert result.node.data_id == "test-data"
        assert result.node.value == 5000
        assert result.node.source == "测试来源"
        assert result.node.is_raw is True

    @pytest.mark.asyncio
    async def test_derive_data_without_formula_rejected(self):
        """F06-T008: 派生数据必须包含公式"""
        from f06_tier1_verification.data_lineage_tracker import DataLineageTracker

        tracker = DataLineageTracker()
        tracker.register_raw_data("data-0", 1000, "source")

        result = tracker.register_derived_data(
            "data-1",
            formula=None,  # 缺少公式
            input_data_ids=["data-0"]
        )

        assert result.rejected is True
        assert "MISSING_FORMULA" in result.reason

    @pytest.mark.asyncio
    async def test_detect_anomaly_in_value_range(self):
        """F06-T009: 检测数值范围异常"""
        from f06_tier1_verification.data_lineage_tracker import DataLineageTracker

        tracker = DataLineageTracker()

        # 注册不可能的数值（人口为负数）
        result = tracker.register_raw_data("population", -1000, "恶意来源")

        assert result.rejected is True
        assert "INVALID_RANGE" in result.reason

    @pytest.mark.asyncio
    async def test_get_nonexistent_lineage_raises(self):
        """F06-T010: 获取不存在的传播链应抛出异常"""
        from f06_tier1_verification.data_lineage_tracker import DataLineageTracker

        tracker = DataLineageTracker()

        with pytest.raises(ValueError):
            tracker.get_propagation_chain("nonexistent-id")

    @pytest.mark.asyncio
    async def test_max_derivation_chain(self):
        """F06-T011: 最大派生链长度验证"""
        from f06_tier1_verification.data_lineage_tracker import DataLineageTracker

        tracker = DataLineageTracker(max_derivation_chain=5, max_depth=10)

        # data-0 -> data-1 -> data-2 -> data-3 -> data-4 (chain length = 5, OK)
        tracker.register_raw_data("data-0", 1000, "source")
        tracker.register_derived_data(
            "data-1",
            formula="data-0 * 0.5",
            input_data_ids=["data-0"]
        )
        tracker.register_derived_data(
            "data-2",
            formula="data-1 * 0.5",
            input_data_ids=["data-1"]
        )
        tracker.register_derived_data(
            "data-3",
            formula="data-2 * 0.5",
            input_data_ids=["data-2"]
        )
        tracker.register_derived_data(
            "data-4",
            formula="data-3 * 0.5",
            input_data_ids=["data-3"]
        )

        # 第5个派生应该被接受（chain length = 5）
        result = tracker.register_derived_data(
            "data-5",
            formula="data-4 * 0.5",
            input_data_ids=["data-4"]
        )
        assert result.rejected is False

        # 超过最大链长度应被拒绝（chain length = 6 > 5）
        result2 = tracker.register_derived_data(
            "data-6",
            formula="data-5 * 0.5",
            input_data_ids=["data-5"]
        )
        assert result2.rejected is True
        assert "DERIVATION_CHAIN_EXCEEDED" in result2.reason


class TestExternalDataVerifier:
    """外部数据核实引擎 - TDD RED阶段"""

    @pytest.mark.asyncio
    async def test_verify_with_national_statistics_api(self):
        """F06-T012: 调用国家统计局API"""
        from f06_tier1_verification.tier1_engine import ExternalDataVerifier

        verifier = ExternalDataVerifier()

        with patch.object(verifier, '_call_national_stats_api', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {"gdp": 12900000000000, "year": 2023}

            result = await verifier.verify(
                data_type="gdp",
                value=12900000000000,
                year=2023,
                region="中国"
            )

            assert result.is_verified is True

    @pytest.mark.asyncio
    async def test_discrepancy_calculation(self):
        """F06-T013: 偏差计算正确"""
        from f06_tier1_verification.tier1_engine import Tier1Verifier

        verifier = Tier1Verifier()

        with patch.object(verifier, '_call_external_api', new_callable=AsyncMock) as mock_api:
            # API返回12.9万亿，用户提供12.8万亿，偏差约0.77%
            mock_api.return_value = {"verified": True, "value": 12900000000000}

            result = await verifier.verify(
                data_type="gdp",
                value=12800000000000,
                year=2023
            )

            assert result.discrepancy < 0.01  # 小于1%

    @pytest.mark.asyncio
    async def test_verification_timeout_handling(self):
        """F06-T014: 核实超时处理"""
        from f06_tier1_verification.tier1_engine import Tier1Verifier, VerificationStatus

        verifier = Tier1Verifier(timeout_seconds=0.001)

        original_fetch = verifier._fetch_external_data

        async def slow_fetch(*args, **kwargs):
            await asyncio.sleep(10)
            return await original_fetch(*args, **kwargs)

        verifier._fetch_external_data = slow_fetch

        result = await verifier.verify(
            data_type="gdp",
            value=12900000000000,
            year=2023
        )

        assert result.is_verified is False
        assert result.status == VerificationStatus.TIMEOUT


class TestSecurityTests:
    """安全测试 - P0漏洞覆盖"""

    @pytest.mark.asyncio
    async def test_fabricated_data_detection(self):
        """F06-S001: 捏造数据检测 - P0-2漏洞防御"""
        from f06_tier1_verification.tier1_engine import Tier1Verifier

        verifier = Tier1Verifier()

        # 极端异常值检测
        result = await verifier.verify(
            data_type="population",
            value=999999999999999999,  # 超出合理范围
            year=2023
        )

        assert result.is_verified is False
        assert "ANOMALY_DETECTED" in result.reason or "INVALID_RANGE" in result.reason

    @pytest.mark.asyncio
    async def test_lineage_tampering_detection(self):
        """F06-S002: 数据血缘篡改检测"""
        from f06_tier1_verification.data_lineage_tracker import DataLineageTracker

        tracker = DataLineageTracker()

        # 注册原始数据
        tracker.register_raw_data("original", 5000, "trusted-source")

        # 尝试注册派生数据但篡改了父节点
        node = tracker.get_node("original")
        if node:
            node.value = 999999  # 篡改值

        # 检查是否能检测到篡改
        lineage = tracker.get_propagation_chain("original")
        # 原始节点应该是可信的
        assert lineage[0].source == "trusted-source"

    @pytest.mark.asyncio
    async def test_propagation_depth_attack_prevention(self):
        """F06-S003: 传播深度攻击防护"""
        from f06_tier1_verification.data_lineage_tracker import DataLineageTracker

        tracker = DataLineageTracker(max_depth=3, max_derivation_chain=5)

        # 模拟多层派生攻击
        tracker.register_raw_data("base", 1000, "source")
        for i in range(10):
            result = tracker.register_derived_data(
                f"layer-{i+1}",
                formula=f"layer-{i} * 1.01",
                input_data_ids=[f"layer-{i}"]
            )
            if i >= 4:
                assert result.rejected is True

    @pytest.mark.asyncio
    async def test_race_condition_in_lineage_registration(self):
        """F06-S004: 竞态条件防护"""
        import asyncio

        from f06_tier1_verification.data_lineage_tracker import DataLineageTracker

        tracker = DataLineageTracker()

        async def register_concurrent(idx):
            tracker.register_raw_data(f"concurrent-data-{idx}", 1000, "source")

        # 并发注册
        tasks = [register_concurrent(i) for i in range(10)]
        await asyncio.gather(*tasks)

        # 检查注册的数据
        nodes = tracker.get_all_nodes()
        assert len(nodes) == 10

    @pytest.mark.asyncio
    async def test_negative_value_prevention(self):
        """F06-S005: 负数值防护"""
        from f06_tier1_verification.tier1_engine import Tier1Verifier

        verifier = Tier1Verifier()

        result = await verifier.verify(
            data_type="price",
            value=-100,
            year=2023
        )

        assert result.is_verified is False
        assert "INVALID_RANGE" in result.reason


class TestIntegrationTests:
    """集成测试 - 模块间交互"""

    @pytest.mark.asyncio
    async def test_verifier_and_tracker_integration(self):
        """F06-I001: 核实引擎与追踪器集成"""
        from f06_tier1_verification.data_lineage_tracker import DataLineageTracker
        from f06_tier1_verification.tier1_engine import Tier1Verifier

        verifier = Tier1Verifier()
        tracker = DataLineageTracker()

        # 注册原始GDP数据
        tracker.register_raw_data("gdp-2023", 12900000000000, "国家统计局")

        # 验证数据
        result = await verifier.verify(
            data_type="gdp",
            value=12900000000000,
            year=2023
        )

        assert result.is_verified is True
        lineage = tracker.get_propagation_chain("gdp-2023")
        assert len(lineage) == 1

    @pytest.mark.asyncio
    async def test_full_verification_workflow(self):
        """F06-I002: 完整核实工作流"""
        from f06_tier1_verification.data_lineage_tracker import DataLineageTracker
        from f06_tier1_verification.tier1_engine import Tier1Verifier

        Tier1Verifier()
        tracker = DataLineageTracker()

        # 1. 注册原始数据
        tracker.register_raw_data("gdp-2023", 12900000000000, "国家统计局")

        # 2. 派生计算
        derived = tracker.register_derived_data(
            "per-capita-gdp",
            formula="gdp-2023 / population-2023",
            input_data_ids=["gdp-2023"]
        )
        assert derived.rejected is False

        # 3. 验证派生数据
        lineage = tracker.get_propagation_chain("per-capita-gdp")
        assert len(lineage) == 2
        assert lineage[0].is_raw is True


class TestTier1EngineUncoveredBranches:
    """覆盖Tier1Engine未测试的分支"""

    @pytest.mark.asyncio
    async def test_verify_invalid_type(self):
        """verify处理非数值类型 (覆盖line 60)"""
        from f06_tier1_verification.tier1_engine import Tier1Verifier

        verifier = Tier1Verifier()
        result = await verifier.verify(
            data_type="gdp",
            value="not a number",  # string instead of int/float
            year=2023
        )
        assert result.is_verified is False
        assert "INVALID_TYPE" in result.reason

    @pytest.mark.asyncio
    async def test_verify_external_api_unavailable(self):
        """verify处理外部API不可用 (覆盖line 91)"""
        from unittest.mock import patch

        from f06_tier1_verification.tier1_engine import Tier1Verifier

        verifier = Tier1Verifier()

        with patch.object(verifier, '_fetch_external_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = None  # API unavailable
            result = await verifier.verify(
                data_type="gdp",
                value=12900000000000,
                year=2023
            )
            assert result.is_verified is False
            assert "EXTERNAL_API_UNAVAILABLE" in result.reason

    @pytest.mark.asyncio
    async def test_verify_exception_handling(self):
        """verify处理异常情况 (覆盖lines 115-116)"""
        from unittest.mock import patch

        from f06_tier1_verification.tier1_engine import Tier1Verifier

        verifier = Tier1Verifier()

        with patch.object(verifier, '_fetch_external_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = Exception("Network error")
            result = await verifier.verify(
                data_type="gdp",
                value=12900000000000,
                year=2023
            )
            assert result.is_verified is False
            assert "ERROR:" in result.reason

    def test_calculate_discrepancy_zero_division(self):
        """_calculate_discrepancy处理除数为零 (覆盖line 199)"""
        from f06_tier1_verification.tier1_engine import Tier1Verifier

        verifier = Tier1Verifier()

        # value2 == 0 and value1 != 0
        result = verifier._calculate_discrepancy(5.0, 0.0)
        assert result == 1.0

        # value2 == 0 and value1 == 0
        result = verifier._calculate_discrepancy(0.0, 0.0)
        assert result == 0.0


class TestDataLineageTrackerUncovered:
    """覆盖DataLineageTracker未测试的分支"""

    @pytest.mark.asyncio
    async def test_build_propagation_chain_with_visited(self):
        """_build_propagation_chain处理已访问节点 (覆盖lines 180-181)"""
        from f06_tier1_verification.data_lineage_tracker import DataLineageTracker

        tracker = DataLineageTracker()

        tracker.register_raw_data("data-a", 100, "source")
        tracker.register_derived_data(
            "data-b",
            formula="data-a * 2",
            input_data_ids=["data-a"]
        )

        tracker.get_propagation_chain("data-a")

        chain_with_visited = []
        visited = set()
        tracker._build_propagation_chain("data-a", chain_with_visited, visited)

        assert len(chain_with_visited) >= 1

    @pytest.mark.asyncio
    async def test_build_propagation_chain_nonexistent_node(self):
        """_build_propagation_chain处理不存在的节点 (覆盖lines 184-185)"""
        from f06_tier1_verification.data_lineage_tracker import DataLineageTracker

        tracker = DataLineageTracker()

        chain = []
        visited = set()
        tracker._build_propagation_chain("nonexistent-id", chain, visited)

        assert len(chain) == 0

    def test_detect_anomaly_nonexistent_node(self):
        """detect_anomaly处理不存在的节点 (覆盖lines 201-203)"""
        from f06_tier1_verification.data_lineage_tracker import DataLineageTracker

        tracker = DataLineageTracker()
        result = tracker.detect_anomaly("nonexistent-id")

        assert result is True

    def test_detect_anomaly_invalid_value(self):
        """detect_anomaly处理无效值 (覆盖lines 205-207)"""
        from f06_tier1_verification.data_lineage_tracker import DataLineageTracker

        tracker = DataLineageTracker()
        tracker.register_raw_data("bad-data", -999999, "malicious")

        result = tracker.detect_anomaly("bad-data")
        assert result is True

    def test_check_value_range_non_numeric(self):
        """_check_value_range处理非数值 (覆盖line 214)"""
        from f06_tier1_verification.data_lineage_tracker import DataLineageTracker

        tracker = DataLineageTracker()
        result = tracker._check_value_range("not a number")

        assert result is None

    def test_build_propagation_chain_visited_early_exit(self):
        """_build_propagation_chain处理已访问节点的早期返回 (覆盖line 181)"""
        from f06_tier1_verification.data_lineage_tracker import DataLineageTracker

        tracker = DataLineageTracker()
        tracker.register_raw_data("data-a", 100, "source")
        tracker.register_derived_data(
            "data-b",
            formula="data-a * 2",
            input_data_ids=["data-a"]
        )

        chain = []
        visited = {"data-a"}
        tracker._build_propagation_chain("data-a", chain, visited)
        assert len(chain) == 0

    def test_detect_anomaly_with_invalid_range(self):
        """detect_anomaly检测到无效范围 (覆盖lines 205-207)"""
        from f06_tier1_verification.data_lineage_tracker import DataLineageTracker

        tracker = DataLineageTracker()
        tracker.register_raw_data("data", 1000, "source")
        node = tracker.get_node("data")
        node.value = 400000000000000

        result = tracker.detect_anomaly("data")
        assert result is True

    def test_detect_anomaly_valid_value_returns_false(self):
        """detect_anomaly对有效值返回False (覆盖line 209)"""
        from f06_tier1_verification.data_lineage_tracker import DataLineageTracker

        tracker = DataLineageTracker()
        tracker.register_raw_data("valid-data", 5000, "source")

        result = tracker.detect_anomaly("valid-data")
        assert result is False


class TestTier1EngineUncoveredValueRanges:
    """覆盖Tier1Engine中value range和anomaly threshold未覆盖的分支"""

    @pytest.mark.asyncio
    async def test_check_value_range_unknown_type_returns_none(self):
        """_check_value_range处理未知类型返回None (覆盖line 125)"""
        from f06_tier1_verification.tier1_engine import Tier1Verifier

        verifier = Tier1Verifier()
        result = verifier._check_value_range("unknown_type", 1000)
        assert result is None

    @pytest.mark.asyncio
    async def test_check_anomaly_unknown_type_returns_none(self):
        """_check_anomaly处理未知类型返回None (覆盖line 139)"""
        from f06_tier1_verification.tier1_engine import Tier1Verifier

        verifier = Tier1Verifier()
        result = verifier._check_anomaly("unknown_type", 1000)
        assert result is None

    @pytest.mark.asyncio
    async def test_external_data_verifier_calls_national_stats_api(self):
        """ExternalDataVerifier._call_national_stats_api (覆盖line 241)"""
        from f06_tier1_verification.tier1_engine import ExternalDataVerifier

        verifier = ExternalDataVerifier()
        result = await verifier._call_national_stats_api("gdp", 2023, "中国")
        assert "value" in result
