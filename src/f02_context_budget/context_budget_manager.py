"""
F02: 上下文预算管理器 - GREEN阶段实现

固定核心60K + 弹性素材40K预算控制
"""

from dataclasses import dataclass


class BudgetError(Exception):
    """预算错误异常"""
    pass


@dataclass
class BudgetResult:
    """预算操作结果"""
    accepted: bool
    rejection_reason: str | None = None
    evicted_material: str | None = None


class ContextBudgetManager:
    """
    上下文预算管理器

    层级结构:
    - L0: 核心上下文 (固定60K tokens)
    - L1: 弹性材料 (上限40K tokens)
    - 总计: 100K tokens
    """

    L0_CORE_BUDGET = 60_000
    L1_MATERIAL_BUDGET = 40_000
    TOTAL_BUDGET = 100_000
    COMPRESSION_THRESHOLD = 0.80

    def __init__(self):
        self._core_context: dict = {}
        self._core_context_tokens: int = 0
        self._materials: dict[str, dict] = {}
        self._material_tokens: dict[str, int] = {}
        self._material_order: list[str] = []
        self._compression_threshold: float = self.COMPRESSION_THRESHOLD
        self._usage_ratio: float = 0.0

    def set_core_context(self, context: dict) -> BudgetResult:
        """
        设置核心上下文 (L0)

        Args:
            context: 包含outline的字典

        Returns:
            BudgetResult: 操作结果
        """
        tokens = self.estimate_tokens(context)

        if tokens > self.L0_CORE_BUDGET:
            return BudgetResult(
                accepted=False,
                rejection_reason="CORE_CONTEXT_EXCEEDED"
            )

        self._core_context = context
        self._core_context_tokens = tokens
        return BudgetResult(accepted=True)

    def add_material(self, chapter_id: str, material: dict) -> BudgetResult:
        """
        添加章节材料 (L1)

        Args:
            chapter_id: 章节ID
            material: 包含reference/text的字典

        Returns:
            BudgetResult: 操作结果
        """
        tokens = self.estimate_tokens(material)

        if tokens > self.L1_MATERIAL_BUDGET:
            return BudgetResult(
                accepted=False,
                rejection_reason="MATERIAL_EXCEEDED"
            )

        evicted_material = None
        while self._get_material_total_tokens() + tokens > self.L1_MATERIAL_BUDGET:
            evicted = self._evict_oldest_material()
            if evicted is None:
                return BudgetResult(
                    accepted=False,
                    rejection_reason="MATERIAL_BUDGET_EXCEEDED"
                )
            evicted_material = evicted

        self._materials[chapter_id] = material
        self._material_tokens[chapter_id] = tokens
        self._material_order.append(chapter_id)

        return BudgetResult(accepted=True, evicted_material=evicted_material)

    def add_content(self, chapter_id: str, content: dict) -> BudgetResult:
        """
        添加内容 (同时检查L0+L1预算)

        Args:
            chapter_id: 章节ID
            content: 包含text的字典

        Returns:
            BudgetResult: 操作结果
        """
        tokens = self.estimate_tokens(content)
        total_tokens = self._get_total_tokens()

        if total_tokens + tokens > self.TOTAL_BUDGET:
            return BudgetResult(
                accepted=False,
                rejection_reason="TOTAL_BUDGET_EXCEEDED"
            )

        result = self.add_material(chapter_id, content)
        if result.accepted and result.evicted_material:
            return result

        return result

    def remove_material(self, chapter_id: str) -> None:
        """移除材料"""
        if chapter_id in self._materials:
            del self._materials[chapter_id]
            del self._material_tokens[chapter_id]
            if chapter_id in self._material_order:
                self._material_order.remove(chapter_id)

    def get_material_size(self, chapter_id: str) -> int:
        """获取材料的token大小"""
        return self._material_tokens.get(chapter_id, 0)

    def get_core_context_size(self) -> int:
        """获取核心上下文大小"""
        return self._core_context_tokens

    def get_total_usage(self) -> int:
        """获取总使用量"""
        return self._get_total_tokens()

    def get_per_chapter_counts(self) -> dict[str, int]:
        """获取每章节token计数"""
        return self._material_tokens.copy()

    def get_material_list(self) -> list[str]:
        """获取材料列表"""
        return list(self._materials.keys())

    def should_compress(self) -> bool:
        """是否应该压缩"""
        return self._usage_ratio >= self._compression_threshold

    def set_usage_ratio(self, ratio: float) -> None:
        """设置使用率 (用于测试)"""
        self._usage_ratio = ratio

    def set_compression_threshold(self, threshold: float) -> None:
        """设置压缩阈值"""
        self._compression_threshold = threshold

    def estimate_tokens(self, content: dict) -> int:
        """
        估算token数量

        简化实现：使用字符数作为token估算
        实际应该使用专门的tokenizer

        Args:
            content: 内容字典

        Returns:
            int: 估算的token数量
        """
        text = (
            content.get("text", "") or
            content.get("ref", "") or
            content.get("reference", "") or
            content.get("outline", "")
        )
        return len(text)

    def _get_total_tokens(self) -> int:
        """获取总token数"""
        return self._core_context_tokens + self._get_material_total_tokens()

    def _get_material_total_tokens(self) -> int:
        """获取材料总token数"""
        return sum(self._material_tokens.values())

    def _evict_oldest_material(self) -> str | None:
        """淘汰最老的材料"""
        while self._material_order:
            oldest = self._material_order.pop(0)
            if oldest in self._materials:
                del self._materials[oldest]
                del self._material_tokens[oldest]
                return oldest
        return None
