"""
F20: LLM-as-Judge评分系统 - 评分标准验证器

验证评分标准和分数的有效性
"""

from typing import Any

from f20_llm_judge.scoring_engine import JUDGE_DIMENSIONS


class RubricValidator:
    """评分标准验证器"""

    def __init__(self, dimensions: dict[str, dict[str, Any]] = None):
        """
        初始化验证器

        Args:
            dimensions: 评分维度配置
        """
        self._dimensions = dimensions or JUDGE_DIMENSIONS

    def validate_rubric(self, rubric: dict[str, Any]) -> bool:
        """
        验证评分标准

        Args:
            rubric: 评分标准字典

        Returns:
            是否有效
        """
        # 检查必需维度
        if not self._has_required_dimensions(rubric):
            return False

        # 检查权重和
        if not self._weights_sum_to_one(rubric):
            return False

        # 检查权重范围
        if not self._weights_in_valid_range(rubric):
            return False

        return True

    def _has_required_dimensions(self, rubric: dict[str, Any]) -> bool:
        """检查是否包含所有必需维度"""
        for dim_key in self._dimensions.keys():
            if dim_key not in rubric:
                return False
        return True

    def _weights_sum_to_one(self, rubric: dict[str, Any]) -> bool:
        """检查权重和是否为1"""
        total_weight = sum(rubric[dim_key].get("weight", 0) for dim_key in self._dimensions.keys())
        return abs(total_weight - 1.0) < 0.001

    def _weights_in_valid_range(self, rubric: dict[str, Any]) -> bool:
        """检查权重是否在有效范围内"""
        for dim_key in self._dimensions.keys():
            if dim_key in rubric:
                weight = rubric[dim_key].get("weight", 0)
                if weight < 0.0 or weight > 1.0:
                    return False
        return True

    def validate_dimension_score(self, score: float) -> bool:
        """
        验证单维度分数

        Args:
            score: 分数值

        Returns:
            是否有效
        """
        return 0.0 <= score <= 1.0

    def validate_all_dimension_scores(self, scores: dict[str, float]) -> tuple[bool, list[str]]:
        """
        验证所有维度分数

        Args:
            scores: 分数字典

        Returns:
            (是否有效, 错误列表)
        """
        errors = []

        for dim_key in self._dimensions.keys():
            if dim_key not in scores:
                errors.append(f"Missing score for dimension: {dim_key}")
                continue

            score = scores[dim_key]
            if not self.validate_dimension_score(score):
                errors.append(f"Score for {dim_key} out of range: {score}")

        return len(errors) == 0, errors

    def get_dimension_descriptions(self) -> dict[str, str]:
        """获取所有维度的描述"""
        return {dim_key: dim_config["description"] for dim_key, dim_config in self._dimensions.items()}
