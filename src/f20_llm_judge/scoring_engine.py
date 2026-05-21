"""
F20: LLM-as-Judge评分系统 - 评分引擎

负责评分维度权重计算和分数验证
"""

from dataclasses import dataclass
from typing import Any

JUDGE_DIMENSIONS: dict[str, dict[str, Any]] = {
    "terminology_consistency": {
        "weight": 0.25,
        "description": "术语使用与术语表的一致性"
    },
    "knowledge_accuracy": {
        "weight": 0.30,
        "description": "知识陈述的准确性"
    },
    "citation_validity": {
        "weight": 0.20,
        "description": "引用的有效性和完整性"
    },
    "logical_coherence": {
        "weight": 0.15,
        "description": "论证逻辑的连贯性"
    },
    "format_compliance": {
        "weight": 0.10,
        "description": "格式规范的遵循程度"
    }
}


@dataclass
class DimensionScore:
    """单维度评分"""
    dimension: str
    score: float
    weight: float


class ScoringEngine:
    """评分引擎"""

    def __init__(self, dimensions: dict[str, dict[str, Any]] = None):
        """
        初始化评分引擎

        Args:
            dimensions: 评分维度配置，默认为JUDGE_DIMENSIONS
        """
        self.dimensions = dimensions or JUDGE_DIMENSIONS

    def calculate_weighted_score(
        self,
        dimension_scores: dict[str, float]
    ) -> float:
        """
        计算加权总分

        Args:
            dimension_scores: 各维度分数字典

        Returns:
            加权总分

        Raises:
            ValueError: 当维度缺失或分数无效时
        """
        # 验证所有维度都有分数
        for dim_key in self.dimensions.keys():
            if dim_key not in dimension_scores:
                raise ValueError(f"Missing score for dimension: {dim_key}")

        # QC-012 Fix: 检查dimension_scores中是否有额外的维度
        for dim_key in dimension_scores.keys():
            if dim_key not in self.dimensions:
                raise ValueError(f"Unknown dimension: {dim_key}. Expected dimensions: {list(self.dimensions.keys())}")

        # 验证分数范围
        for dim_key, score in dimension_scores.items():
            if not isinstance(score, int | float):
                raise ValueError(f"Score for {dim_key} must be numeric")
            if score < 0.0 or score > 1.0:
                raise ValueError(
                    f"Score for {dim_key} must be between 0.0 and 1.0, got {score}"
                )

        # 计算加权分数
        total_score = 0.0
        for dim_key, dim_config in self.dimensions.items():
            weight = dim_config["weight"]
            score = dimension_scores[dim_key]
            total_score += score * weight

        return round(total_score, 4)

    def get_dimension_scores_with_weights(
        self,
        dimension_scores: dict[str, float]
    ) -> list[DimensionScore]:
        """
        获取带权重的维度分数详情

        Args:
            dimension_scores: 各维度分数字典

        Returns:
            维度分数详情列表
        """
        result = []
        for dim_key, dim_config in self.dimensions.items():
            if dim_key in dimension_scores:
                result.append(DimensionScore(
                    dimension=dim_key,
                    score=dimension_scores[dim_key],
                    weight=dim_config["weight"]
                ))
        return result

    def validate_dimension_scores(
        self,
        dimension_scores: dict[str, float]
    ) -> tuple[bool, list[str]]:
        """
        验证维度分数

        Args:
            dimension_scores: 各维度分数字典

        Returns:
            (是否有效, 错误信息列表)
        """
        errors = []

        # 检查维度完整性
        for dim_key in self.dimensions.keys():
            if dim_key not in dimension_scores:
                errors.append(f"Missing dimension: {dim_key}")

        # QC-012 Fix: 检查是否有额外的未知维度
        for dim_key in dimension_scores.keys():
            if dim_key not in self.dimensions:
                errors.append(f"Unknown dimension: {dim_key}")

        # 检查分数范围
        for dim_key, score in dimension_scores.items():
            if score < 0.0 or score > 1.0:
                errors.append(
                    f"Score for {dim_key} out of range: {score}"
                )

        return len(errors) == 0, errors

    def get_weight_for_dimension(self, dimension: str) -> float:
        """获取维度的权重"""
        if dimension in self.dimensions:
            return self.dimensions[dimension]["weight"]
        return 0.0

    def get_all_dimensions(self) -> dict[str, dict[str, Any]]:
        """获取所有维度配置"""
        return self.dimensions.copy()
