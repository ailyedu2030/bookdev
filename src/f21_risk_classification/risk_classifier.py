"""
F21: 风险分级复核系统 - 风险分级器

根据质量分数进行风险分级
"""

from dataclasses import dataclass
from typing import Any

from f21_risk_classification.risk_thresholds import (
    RISK_LEVELS,
    get_risk_level_for_score,
    is_auto_approvable,
)


@dataclass
class RiskClassification:
    """风险分类结果"""
    level: str
    review_ratio: float
    auto_approve: bool


class RiskClassifier:
    """风险分级器"""

    def __init__(self, risk_levels: dict[str, dict[str, Any]] = None):
        """
        初始化风险分级器

        Args:
            risk_levels: 风险等级配置
        """
        self._risk_levels = risk_levels or RISK_LEVELS

    def classify(self, score: float) -> str:
        """
        根据质量分数分类风险等级

        Args:
            score: 质量分数 (0-1)

        Returns:
            风险等级

        Raises:
            ValueError: 分数超出有效范围时
        """
        if score < 0.0 or score > 1.0:
            raise ValueError(f"Score must be between 0.0 and 1.0, got {score}")

        return get_risk_level_for_score(score)

    def classify_with_metadata(self, score: float) -> dict[str, Any]:
        """
        带元数据的风险分类

        Args:
            score: 质量分数 (0-1)

        Returns:
            包含风险等级和配置的字典
        """
        level = self.classify(score)
        config = self._risk_levels[level]

        return {
            "level": level,
            "review_ratio": config["review_ratio"],
            "auto_approve": config["auto_approve"]
        }

    def get_review_ratio(self, level: str) -> float | None:
        """
        获取风险等级的复核比例

        Args:
            level: 风险等级

        Returns:
            复核比例，如果等级无效返回None
        """
        if level not in self._risk_levels:
            return None
        return self._risk_levels[level]["review_ratio"]

    def get_review_ratio_for_score(self, score: float) -> float:
        """
        根据分数获取复核比例

        Args:
            score: 质量分数

        Returns:
            复核比例
        """
        level = self.classify(score)
        ratio = self.get_review_ratio(level)
        return ratio if ratio is not None else 1.0

    def is_auto_approvable(self, level: str) -> bool:
        """
        判断风险等级是否可自动批准

        Args:
            level: 风险等级

        Returns:
            是否可自动批准
        """
        return is_auto_approvable(level)

    def is_auto_approvable_by_score(self, score: float) -> bool:
        """
        根据分数判断是否可自动批准

        Args:
            score: 质量分数

        Returns:
            是否可自动批准
        """
        level = self.classify(score)
        return self.is_auto_approvable(level)

    def get_score_range(self, level: str) -> tuple[float, float] | None:
        """
        获取风险等级的分数范围

        Args:
            level: 风险等级

        Returns:
            (最小分数, 最大分数)元组，无效时返回None
        """
        if level not in self._risk_levels:
            return None
        return tuple(self._risk_levels[level]["score_range"])
