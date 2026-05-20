"""
F16: 统计抽样验证引擎
基于统计学的抽样验证，确保样本代表性
"""
from f16_statistical_sampling.sampling_engine import (
    StatisticalSamplingEngine,
    Chapter,
    ChapterType,
)
from f16_statistical_sampling.confidence_calculator import (
    ConfidenceCalculator,
    ConfidenceInterval,
)
from f16_statistical_sampling.sample_validator import (
    SampleValidator,
    ValidationResult,
    BiasDetectionResult,
)

__all__ = [
    "StatisticalSamplingEngine",
    "Chapter",
    "ChapterType",
    "ConfidenceCalculator",
    "ConfidenceInterval",
    "SampleValidator",
    "ValidationResult",
    "BiasDetectionResult",
]
