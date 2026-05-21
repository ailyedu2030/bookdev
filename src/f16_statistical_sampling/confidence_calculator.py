"""
F16: 置信度计算器
计算置信区间和误差范围
"""
import math
from dataclasses import dataclass


@dataclass
class ConfidenceInterval:
    lower_bound: float
    upper_bound: float
    confidence_level: float
    margin_of_error: float


class ConfidenceCalculator:
    """置信度计算器"""

    Z_SCORES = {
        0.90: 1.645,
        0.95: 1.96,
        0.99: 2.576,
    }

    def __init__(self):
        pass

    def calculate_confidence_interval(
        self, sample_mean: float, sample_std: float, sample_size: int, confidence_level: float = 0.95
    ) -> ConfidenceInterval:
        """计算置信区间"""
        if sample_size <= 0:
            raise ValueError("Sample size must be positive")
        if sample_std < 0:
            raise ValueError("Standard deviation cannot be negative")

        z = self.Z_SCORES.get(confidence_level, 1.96)

        standard_error = sample_std / math.sqrt(sample_size)

        margin = z * standard_error

        return ConfidenceInterval(
            lower_bound=sample_mean - margin,
            upper_bound=sample_mean + margin,
            confidence_level=confidence_level,
            margin_of_error=margin,
        )

    def calculate_margin_of_error(
        self, sample_proportion: float, sample_size: int, confidence_level: float = 0.95
    ) -> float:
        """计算误差范围"""
        if sample_size <= 0:
            raise ValueError("Sample size must be positive")
        if not 0 <= sample_proportion <= 1:
            raise ValueError("Sample proportion must be between 0 and 1")

        z = self.Z_SCORES.get(confidence_level, 1.96)

        margin = z * math.sqrt((sample_proportion * (1 - sample_proportion)) / sample_size)

        return margin

    def sample_size_from_margin_of_error(
        self, margin_of_error: float, population_proportion: float = 0.5, confidence_level: float = 0.95
    ) -> int:
        """从误差范围反推样本量"""
        if margin_of_error <= 0 or margin_of_error >= 1:
            raise ValueError("Margin of error must be between 0 and 1")
        if not 0 <= population_proportion <= 1:
            raise ValueError("Population proportion must be between 0 and 1")

        z = self.Z_SCORES.get(confidence_level, 1.96)

        p = population_proportion
        e = margin_of_error

        n = (z**2 * p * (1 - p)) / (e**2)

        return int(math.ceil(n))

    def calculate_required_sample_size(
        self,
        population_size: int,
        confidence_level: float = 0.95,
        margin_of_error: float = 0.05,
        population_proportion: float = 0.5,
    ) -> int:
        """计算有限总体所需的样本量"""
        if population_size <= 0:
            raise ValueError("Population size must be positive")

        z = self.Z_SCORES.get(confidence_level, 1.96)
        p = population_proportion
        e = margin_of_error

        n0 = (z**2 * p * (1 - p)) / (e**2)

        n = n0 / (1 + (n0 - 1) / population_size)

        return int(math.ceil(n))

    def calculate_standard_error(self, sample_std: float, sample_size: int) -> float:
        """计算标准误差"""
        if sample_size <= 0:
            raise ValueError("Sample size must be positive")
        if sample_std < 0:
            raise ValueError("Standard deviation cannot be negative")

        return sample_std / math.sqrt(sample_size)

    def calculate_z_score(self, confidence_level: float) -> float:
        """获取Z分数"""
        if confidence_level not in self.Z_SCORES:
            raise ValueError(
                f"Confidence level {confidence_level} not supported. " f"Supported levels: {list(self.Z_SCORES.keys())}"
            )
        return self.Z_SCORES[confidence_level]
