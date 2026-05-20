"""
F02: 上下文预算管理器 - TDD RED阶段测试

按照TDD原则：
1. RED: 写失败测试
2. GREEN: 写最简实现让测试通过
3. Refactor: 优化代码质量
"""

import pytest
from dataclasses import dataclass


@dataclass
class BudgetResult:
    """预算操作结果"""
    accepted: bool
    rejection_reason: str | None = None
    evicted_material: str | None = None


class TestContextBudgetManager:
    """上下文预算管理器基础测试"""

    def test_total_budget_limit_100k_tokens(self):
        """F02-T001: 总预算上限100K Tokens"""
        from f02_context_budget.context_budget_manager import ContextBudgetManager

        manager = ContextBudgetManager()
        manager.set_core_context({"outline": "x" * 60_000})
        result = manager.add_content("chapter_1", {"text": "x" * 50_000})

        assert result.accepted is False
        assert "TOTAL_BUDGET_EXCEEDED" in result.rejection_reason

    def test_l0_core_context_fixed_60k(self):
        """F02-T002: L0核心上下文固定60K"""
        from f02_context_budget.context_budget_manager import ContextBudgetManager

        manager = ContextBudgetManager()
        result = manager.set_core_context({"outline": "x" * 60_000})

        assert result.accepted is True
        assert manager.get_core_context_size() == 60_000

    def test_l0_core_context_cannot_exceed_60k(self):
        """F02-T003: L0核心上下文不能超过60K"""
        from f02_context_budget.context_budget_manager import ContextBudgetManager

        manager = ContextBudgetManager()
        result = manager.set_core_context({"outline": "x" * 70_000})

        assert result.accepted is False
        assert "CORE_CONTEXT_EXCEEDED" in result.rejection_reason

    def test_l1_elastic_material_max_40k(self):
        """F02-T004: L1弹性材料上限40K"""
        from f02_context_budget.context_budget_manager import ContextBudgetManager

        manager = ContextBudgetManager()
        result = manager.add_material("ch01", {"reference": "x" * 40_000})

        assert result.accepted is True
        assert manager.get_material_size("ch01") == 40_000

    def test_budget_exceeded_triggers_rag_eviction(self):
        """F02-T005: 预算超限时触发RAG淘汰"""
        from f02_context_budget.context_budget_manager import ContextBudgetManager

        manager = ContextBudgetManager()
        for i in range(4):
            manager.add_material(f"ch_{i}", {"ref": "x" * 10_000})

        result = manager.add_material("ch_4", {"ref": "x" * 10_000})

        assert result.evicted_material == "ch_0"

    def test_context_compression_when_near_limit(self):
        """F02-T006: 接近上限时触发压缩"""
        from f02_context_budget.context_budget_manager import ContextBudgetManager

        manager = ContextBudgetManager()
        manager.set_usage_ratio(0.95)

        assert manager.should_compress() is True

    def test_per_chapter_token_counting(self):
        """F02-T007: 按章节Token计数"""
        from f02_context_budget.context_budget_manager import ContextBudgetManager

        manager = ContextBudgetManager()
        manager.add_material("ch01", {"text": "x" * 5000})

        counts = manager.get_per_chapter_counts()
        assert counts["ch01"] == 5000

    def test_add_content_within_budget(self):
        """F02-T008: 在预算范围内添加内容"""
        from f02_context_budget.context_budget_manager import ContextBudgetManager

        manager = ContextBudgetManager()
        result = manager.add_content("ch01", {"text": "x" * 5000})

        assert result.accepted is True
        assert result.rejection_reason is None

    def test_l1_material_individual_chapter_limit(self):
        """F02-T009: L1单章节材料限制"""
        from f02_context_budget.context_budget_manager import ContextBudgetManager

        manager = ContextBudgetManager()
        result = manager.add_material("ch01", {"reference": "x" * 50_000})

        assert result.accepted is False
        assert "MATERIAL_EXCEEDED" in result.rejection_reason


class TestContextBudgetManagerEviction:
    """淘汰策略测试"""

    def test_oldest_material_evicted_first(self):
        """F02-T010: 最老材料最先被淘汰"""
        from f02_context_budget.context_budget_manager import ContextBudgetManager

        manager = ContextBudgetManager()
        manager.add_material("ch_0", {"ref": "x" * 10_000})
        manager.add_material("ch_1", {"ref": "x" * 10_000})
        manager.add_material("ch_2", {"ref": "x" * 10_000})
        result = manager.add_material("ch_3", {"ref": "x" * 10_000})  # 总共40_000

        assert result.accepted is True
        assert result.evicted_material is None  # 恰好等于限制，不淘汰

        # 但当超过限制时，淘汰最老的
        result2 = manager.add_material("ch_4", {"ref": "x" * 10_000})
        assert result2.evicted_material == "ch_0"

    def test_multiple_evictions_when_needed(self):
        """F02-T011: 需要时触发多次淘汰"""
        from f02_context_budget.context_budget_manager import ContextBudgetManager

        manager = ContextBudgetManager()
        for i in range(10):
            manager.add_material(f"ch_{i}", {"ref": "x" * 10_000})

        assert manager.get_material_size("ch_0") == 0
        assert manager.get_material_size("ch_9") > 0


class TestContextBudgetManagerCompression:
    """压缩策略测试"""

    def test_should_compress_at_90_percent(self):
        """F02-T012: 90%使用率时应压缩"""
        from f02_context_budget.context_budget_manager import ContextBudgetManager

        manager = ContextBudgetManager()
        manager.set_usage_ratio(0.90)

        assert manager.should_compress() is True

    def test_should_not_compress_at_70_percent(self):
        """F02-T013: 70%使用率时不压缩"""
        from f02_context_budget.context_budget_manager import ContextBudgetManager

        manager = ContextBudgetManager()
        manager.set_usage_ratio(0.70)

        assert manager.should_compress() is False

    def test_compression_threshold_is_configurable(self):
        """F02-T014: 压缩阈值可配置"""
        from f02_context_budget.context_budget_manager import ContextBudgetManager

        manager = ContextBudgetManager()
        manager.set_compression_threshold(0.85)
        manager.set_usage_ratio(0.86)

        assert manager.should_compress() is True


class TestContextBudgetManagerRetrieval:
    """检索测试"""

    def test_get_total_usage(self):
        """F02-T015: 获取总使用量"""
        from f02_context_budget.context_budget_manager import ContextBudgetManager

        manager = ContextBudgetManager()
        manager.add_material("ch01", {"text": "x" * 5000})
        manager.add_material("ch02", {"text": "y" * 3000})

        total = manager.get_total_usage()
        assert total == 8000

    def test_get_material_list(self):
        """F02-T016: 获取材料列表"""
        from f02_context_budget.context_budget_manager import ContextBudgetManager

        manager = ContextBudgetManager()
        manager.add_material("ch01", {"text": "x"})
        manager.add_material("ch02", {"text": "y"})

        materials = manager.get_material_list()
        assert "ch01" in materials
        assert "ch02" in materials

    def test_remove_material(self):
        """F02-T017: 移除材料"""
        from f02_context_budget.context_budget_manager import ContextBudgetManager

        manager = ContextBudgetManager()
        manager.add_material("ch01", {"text": "x" * 5000})

        manager.remove_material("ch01")

        assert manager.get_material_size("ch01") == 0
        assert "ch01" not in manager.get_material_list()


class TestContextBudgetManagerBudgetAllocation:
    """预算分配测试"""

    def test_core_and_material_budgets_are_separate(self):
        """F02-T018: 核心预算和材料预算分离"""
        from f02_context_budget.context_budget_manager import ContextBudgetManager

        manager = ContextBudgetManager()
        manager.set_core_context({"outline": "x" * 60_000})
        result = manager.add_material("ch01", {"ref": "x" * 40_000})

        assert result.accepted is True

    def test_combined_budget_limit(self):
        """F02-T019: 组合预算限制"""
        from f02_context_budget.context_budget_manager import ContextBudgetManager

        manager = ContextBudgetManager()
        manager.set_core_context({"outline": "x" * 60_000})

        result = manager.add_content("ch01", {"text": "x" * 50_000})

        assert result.accepted is False
        assert "TOTAL_BUDGET_EXCEEDED" in result.rejection_reason


class TestContextBudgetManagerEdgeCases:
    """边界条件测试"""

    def test_empty_content(self):
        """F02-T020: 空内容"""
        from f02_context_budget.context_budget_manager import ContextBudgetManager

        manager = ContextBudgetManager()
        result = manager.add_content("ch01", {"text": ""})

        assert result.accepted is True

    def test_zero_token_content(self):
        """F02-T021: 零Token内容"""
        from f02_context_budget.context_budget_manager import ContextBudgetManager

        manager = ContextBudgetManager()
        result = manager.add_content("ch01", {"text": ""})

        assert result.accepted is True
        assert manager.get_total_usage() == 0

    def test_exactly_at_limit(self):
        """F02-T022: 恰好达到限制"""
        from f02_context_budget.context_budget_manager import ContextBudgetManager

        manager = ContextBudgetManager()
        result = manager.add_material("ch01", {"text": "x" * 40_000})

        assert result.accepted is True

    def test_remove_nonexistent_material(self):
        """F02-T023: 移除不存在的材料"""
        from f02_context_budget.context_budget_manager import ContextBudgetManager

        manager = ContextBudgetManager()
        manager.remove_material("nonexistent")

        # 不应抛出异常
        assert True


class TestContextBudgetManagerEvictionEdgeCases:
    """淘汰策略边界测试"""

    def test_evict_when_material_order_becomes_empty(self):
        """F02-T027: 材料顺序列表为空时添加材料"""
        from f02_context_budget.context_budget_manager import ContextBudgetManager

        manager = ContextBudgetManager()
        manager.add_material("ch_0", {"ref": "x" * 10_000})
        manager.add_material("ch_1", {"ref": "x" * 10_000})
        manager.add_material("ch_2", {"ref": "x" * 10_000})
        manager.add_material("ch_3", {"ref": "x" * 10_000})

        manager.remove_material("ch_0")
        manager.remove_material("ch_1")
        manager.remove_material("ch_2")
        manager.remove_material("ch_3")

        result = manager.add_material("ch_new", {"ref": "x" * 5000})

        assert result.accepted is True
        assert result.evicted_material is None

    def test_evicted_material_is_recorded(self):
        """F02-T028: 验证淘汰的材料被正确记录"""
        from f02_context_budget.context_budget_manager import ContextBudgetManager

        manager = ContextBudgetManager()
        manager.add_material("ch_0", {"ref": "x" * 10_000})
        manager.add_material("ch_1", {"ref": "x" * 10_000})
        manager.add_material("ch_2", {"ref": "x" * 10_000})
        manager.add_material("ch_3", {"ref": "x" * 10_000})

        result = manager.add_material("ch_4", {"ref": "x" * 10_000})

        assert result.accepted is True
        assert result.evicted_material == "ch_0"

    def test_evict_oldest_material_returns_none_when_order_empty(self):
        """F02-T029: _evict_oldest_material在顺序为空时返回None"""
        from f02_context_budget.context_budget_manager import ContextBudgetManager

        manager = ContextBudgetManager()
        manager.add_material("ch_0", {"ref": "x" * 5000})
        manager.remove_material("ch_0")

        result = manager.add_material("ch_new", {"ref": "x" * 5000})

        assert result.accepted is True
        assert result.evicted_material is None


class TestContextBudgetManagerAddContent:
    """add_content方法测试"""

    def test_add_content_with_eviction_recorded(self):
        """F02-T030: add_content在发生淘汰时返回evicted_material"""
        from f02_context_budget.context_budget_manager import ContextBudgetManager

        manager = ContextBudgetManager()
        manager.set_core_context({"outline": "core"})
        for i in range(3):
            manager.add_material(f"ch_{i}", {"ref": "x" * 10_000})

        result = manager.add_content("ch_new", {"text": "x" * 10_000})

        assert result.accepted is True

    def test_add_material_exceeds_budget_after_eviction(self):
        """F02-T031: 材料本身超过预算且无法通过淘汰满足 (覆盖line 93)"""
        from f02_context_budget.context_budget_manager import ContextBudgetManager

        manager = ContextBudgetManager()
        for i in range(3):
            manager.add_material(f"ch_{i}", {"ref": "x" * 10_000})

        result = manager.add_material("ch_huge", {"ref": "x" * 50_000})

        assert result.accepted is False
        assert "MATERIAL_EXCEEDED" in result.rejection_reason

    def test_add_content_returns_result_with_evicted_material(self):
        """F02-T032: add_content在有淘汰时直接返回结果 (覆盖line 127)"""
        from f02_context_budget.context_budget_manager import ContextBudgetManager

        manager = ContextBudgetManager()
        for i in range(4):
            manager.add_material(f"ch_{i}", {"ref": "x" * 10_000})

        result = manager.add_content("ch_new", {"text": "x" * 10_000})

        assert result.accepted is True
        assert result.evicted_material is not None

    def test_evict_oldest_material_returns_none_when_all_removed(self):
        """F02-T033: _evict_oldest_material在所有材料移除后返回None (覆盖line 208)"""
        from f02_context_budget.context_budget_manager import ContextBudgetManager

        manager = ContextBudgetManager()
        manager.add_material("ch_0", {"ref": "x" * 5000})
        manager.remove_material("ch_0")
        manager._material_order.clear()

        result = manager._evict_oldest_material()

        assert result is None


class TestContextBudgetManagerTokenEstimation:
    """Token估算测试"""

    def test_token_estimation_for_chinese(self):
        """F02-T024: 中文Token估算"""
        from f02_context_budget.context_budget_manager import ContextBudgetManager

        manager = ContextBudgetManager()
        chinese_text = "人工智能是研究、开发用于模拟、延伸和扩展人的智能的理论、方法、技术..."

        size = manager.estimate_tokens({"text": chinese_text})
        assert size > 0

    def test_token_estimation_for_english(self):
        """F02-T025: 英文Token估算"""
        from f02_context_budget.context_budget_manager import ContextBudgetManager

        manager = ContextBudgetManager()
        english_text = "Artificial Intelligence is the simulation of human intelligence by machines."

        size = manager.estimate_tokens({"text": english_text})
        assert size > 0

    def test_token_estimation_consistency(self):
        """F02-T026: Token估算一致性"""
        from f02_context_budget.context_budget_manager import ContextBudgetManager

        manager = ContextBudgetManager()
        text = "test content"

        size1 = manager.estimate_tokens({"text": text})
        size2 = manager.estimate_tokens({"text": text})

        assert size1 == size2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])