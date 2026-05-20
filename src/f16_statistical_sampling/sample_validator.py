"""
F16: 样本验证器
验证样本的代表性、有效性和无偏性
"""
import math
from dataclasses import dataclass
from typing import List, Dict, Optional, Set


@dataclass
class ValidationResult:
    is_valid: bool
    score: float
    message: str


@dataclass
class BiasDetectionResult:
    is_biased: bool
    bias_score: float
    bias_type: Optional[str] = None
    details: Optional[str] = None


class SampleValidator:
    """样本验证器"""

    MINIMUM_SAMPLE_SIZE = 3

    def __init__(self, minimum_sample_size: int = 3):
        self.minimum_sample_size = minimum_sample_size

    def validate_representativeness(
        self,
        population: List[float],
        sample: List[float]
    ) -> ValidationResult:
        """验证样本代表性"""
        if not population or not sample:
            return ValidationResult(
                is_valid=False,
                score=0.0,
                message="Empty population or sample"
            )

        pop_mean = sum(population) / len(population)
        sample_mean = sum(sample) / len(sample)

        if pop_mean == 0:
            return ValidationResult(
                is_valid=False,
                score=0.0,
                message="Population mean is zero"
            )

        relative_diff = abs(sample_mean - pop_mean) / abs(pop_mean)

        score = max(0, 1 - relative_diff)

        is_valid = score >= 0.8

        return ValidationResult(
            is_valid=is_valid,
            score=score,
            message=f"Sample mean: {sample_mean:.4f}, Population mean: {pop_mean:.4f}"
        )

    def validate_minimum_size(
        self,
        population: List,
        sample: List
    ) -> ValidationResult:
        """验证最小样本量"""
        if len(sample) < self.minimum_sample_size:
            return ValidationResult(
                is_valid=False,
                score=0.0,
                message=f"Sample size {len(sample)} is too small. Minimum is {self.minimum_sample_size}"
            )

        recommended_size = self._calculate_recommended_size(len(population))

        if len(sample) < recommended_size:
            score = len(sample) / recommended_size
            return ValidationResult(
                is_valid=True,
                score=score,
                message=f"Sample size {len(sample)} is below recommended {recommended_size}"
            )

        return ValidationResult(
            is_valid=True,
            score=1.0,
            message=f"Sample size {len(sample)} is adequate"
        )

    def validate_stratification_balance(
        self,
        population_strata: Dict[str, List],
        sample_strata: Dict[str, List]
    ) -> ValidationResult:
        """验证分层平衡"""
        if set(population_strata.keys()) != set(sample_strata.keys()):
            return ValidationResult(
                is_valid=False,
                score=0.0,
                message="Strata mismatch between population and sample"
            )

        scores: List[float] = []

        for stratum in population_strata:
            pop_size = len(population_strata[stratum])
            sample_size = len(sample_strata.get(stratum, []))

            if pop_size == 0:
                continue

            pop_ratio = pop_size / sum(len(v) for v in population_strata.values())
            sample_ratio = sample_size / sum(len(v) for v in sample_strata.values()) if sample_strata else 0

            stratum_score = 1 - abs(pop_ratio - sample_ratio) / pop_ratio if pop_ratio > 0 else 0
            scores.append(max(0, stratum_score))

        if not scores:
            return ValidationResult(
                is_valid=False,
                score=0.0,
                message="No valid strata to compare"
            )

        avg_score = sum(scores) / len(scores)
        is_valid = avg_score >= 0.8

        return ValidationResult(
            is_valid=is_valid,
            score=avg_score,
            message=f"Stratification balance score: {avg_score:.4f}"
        )

    def detect_bias(
        self,
        population: List,
        sample: List
    ) -> BiasDetectionResult:
        """检测抽样偏差"""
        if not population or not sample:
            return BiasDetectionResult(
                is_biased=True,
                bias_score=1.0,
                bias_type="empty",
                details="Empty population or sample"
            )

        pop_sorted = sorted(population)
        sample_sorted = sorted(sample)

        pop_median = self._median(pop_sorted)
        sample_median = self._median(sample_sorted)

        median_diff = abs(sample_median - pop_median) / pop_median if pop_median != 0 else 0

        pop_std = self._std(population)
        sample_std = self._std(sample)

        variance_ratio = sample_std / pop_std if pop_std > 0 else 0

        range_pop = max(population) - min(population) if population else 0
        range_sample = max(sample) - min(sample) if sample else 0
        coverage_ratio = range_sample / range_pop if range_pop > 0 else 0

        bias_score = 0.0

        if median_diff > 0.1:
            bias_score += 0.3
        if variance_ratio < 0.5 or variance_ratio > 2.0:
            bias_score += 0.3
        if coverage_ratio < 0.5:
            bias_score += 0.4

        is_biased = bias_score > 0.3

        bias_type = None
        if bias_score > 0:
            if median_diff > 0.1:
                bias_type = "central_tendency"
            elif variance_ratio < 0.5:
                bias_type = "low_variance"
            elif variance_ratio > 2.0:
                bias_type = "high_variance"
            elif coverage_ratio < 0.5:
                bias_type = "range_restriction"

        return BiasDetectionResult(
            is_biased=is_biased,
            bias_score=bias_score,
            bias_type=bias_type,
            details=f"Median diff: {median_diff:.3f}, Variance ratio: {variance_ratio:.3f}, Coverage: {coverage_ratio:.3f}"
        )

    def validate_sample_quality(
        self,
        population: List[float],
        sample: List[float],
        strata: Optional[Dict[str, List]] = None
    ) -> Dict[str, ValidationResult]:
        """综合样本质量验证"""
        results = {}

        results["representativeness"] = self.validate_representativeness(population, sample)
        results["minimum_size"] = self.validate_minimum_size(population, sample)

        if strata:
            sample_strata = {}
            pop_size = len(population)
            for i, val in enumerate(sample):
                stratum = list(strata.keys())[i % len(strata)]
                if stratum not in sample_strata:
                    sample_strata[stratum] = []
                sample_strata[stratum].append(val)

            results["stratification"] = self.validate_stratification_balance(strata, sample_strata)

        return results

    def _median(self, sorted_list: List) -> float:
        """计算中位数"""
        n = len(sorted_list)
        if n == 0:
            return 0
        if n % 2 == 0:
            return (sorted_list[n // 2 - 1] + sorted_list[n // 2]) / 2
        return sorted_list[n // 2]

    def _std(self, data: List) -> float:
        """计算标准差"""
        if not data:
            return 0
        mean = sum(data) / len(data)
        variance = sum((x - mean) ** 2 for x in data) / len(data)
        return math.sqrt(variance)

    def _calculate_recommended_size(self, population_size: int) -> int:
        """计算推荐样本量"""
        if population_size <= 100:
            return max(10, population_size // 10)
        if population_size <= 1000:
            return max(30, population_size // 20)
        return max(50, int(math.sqrt(population_size)))
