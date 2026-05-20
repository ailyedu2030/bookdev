"""
F30: Golden Dataset系统 - 样本评估器

评估样本质量和校准LLM评判器
"""

import json
import os
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from f30_golden_dataset.dataset_builder import DatasetBuilder, GoldenSample
from f30_golden_dataset.sample_manager import SampleManager


@dataclass
class EvaluationResult:
    """评估结果"""
    overall_score: float
    dimension_scores: Dict[str, float]
    has_hallucinations: bool = False
    has_regulation_errors: bool = False
    detected_hallucinations: List[Dict[str, Any]] = None
    detected_errors: List[Dict[str, Any]] = None


@dataclass
class CalibrationResult:
    """校准结果"""
    correlation: float
    bias: float
    samples_evaluated: int


class GoldenDatasetEvaluator:
    """Golden Dataset评估器"""

    def __init__(self, samples_dir: str = None):
        """
        初始化评估器

        Args:
            samples_dir: 样本文件目录
        """
        self._samples_dir = samples_dir
        self._builder = DatasetBuilder(samples_dir)
        self._manager = SampleManager(samples_dir)

    def evaluate(self, sample: GoldenSample) -> EvaluationResult:
        """
        评估样本

        Args:
            sample: Golden样本

        Returns:
            评估结果
        """
        if isinstance(sample, dict):
            sample = GoldenSample(
                sample_id=sample["sample_id"],
                quality_level=sample["quality_level"],
                expected_score=sample["expected_score"],
                content=sample.get("content", {}),
                quality_metrics=sample.get("quality_metrics", {}),
                metadata=sample.get("metadata", {})
            )

        dimension_scores = sample.quality_metrics.copy()
        overall_score = sample.expected_score

        return EvaluationResult(
            overall_score=overall_score,
            dimension_scores=dimension_scores
        )

    def detect_hallucinations(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        检测幻觉内容

        Args:
            sample: 样本字典

        Returns:
            幻觉检测结果
        """
        hallucination_markers = sample.get("hallucination_markers", [])
        content_text = json.dumps(sample.get("content", {}))

        detected = []
        for marker in hallucination_markers:
            detected.append({
                "type": marker.get("type"),
                "location": marker.get("location"),
                "content": marker.get("content"),
                "issue": marker.get("issue")
            })

        return {
            "has_hallucinations": len(detected) > 0,
            "detected_hallucinations": detected,
            "total_count": len(detected)
        }

    def detect_regulation_errors(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        检测法规错误

        Args:
            sample: 样本字典

        Returns:
            法规错误检测结果
        """
        regulation_errors = sample.get("regulation_errors", [])

        detected = []
        for error in regulation_errors:
            detected.append({
                "type": error.get("type"),
                "law": error.get("law"),
                "cited_article": error.get("cited_article"),
                "issue": error.get("issue")
            })

        return {
            "has_errors": len(detected) > 0,
            "detected_errors": detected,
            "total_count": len(detected)
        }

    def calibrate_judge(
        self,
        llm_results: List[Dict[str, Any]]
    ) -> CalibrationResult:
        """
        使用样本校准评判器

        Args:
            llm_results: LLM评判结果列表

        Returns:
            校准结果
        """
        if not llm_results:
            return CalibrationResult(
                correlation=0.0,
                bias=0.0,
                samples_evaluated=0
            )

        samples = self._manager.list_all_sample_ids()
        expected_scores = []
        llm_scores = []

        for result in llm_results:
            sample_id = result.get("sample_id")
            if sample_id in samples:
                sample = self._manager.get_sample_by_id(sample_id)
                if sample:
                    expected_scores.append(sample.expected_score)
                    llm_scores.append(result.get("overall_score", 0.0))

        if len(expected_scores) < 2:
            return CalibrationResult(
                correlation=0.0,
                bias=0.0,
                samples_evaluated=len(expected_scores)
            )

        # 计算相关性
        correlation = self._calculate_correlation(expected_scores, llm_scores)

        # 计算偏差
        total_bias = sum(
            llm - expected
            for llm, expected in zip(llm_scores, expected_scores)
        )
        bias = total_bias / len(expected_scores)

        return CalibrationResult(
            correlation=correlation,
            bias=bias,
            samples_evaluated=len(expected_scores)
        )

    def _calculate_correlation(
        self,
        x: List[float],
        y: List[float]
    ) -> float:
        """
        计算皮尔逊相关系数

        Args:
            x: 列表1
            y: 列表2

        Returns:
            相关系数
        """
        n = len(x)
        if n < 2:
            return 0.0

        mean_x = sum(x) / n
        mean_y = sum(y) / n

        numerator = sum(
            (x[i] - mean_x) * (y[i] - mean_y)
            for i in range(n)
        )

        sum_sq_x = sum((xi - mean_x) ** 2 for xi in x)
        sum_sq_y = sum((yi - mean_y) ** 2 for yi in y)

        denominator = (sum_sq_x * sum_sq_y) ** 0.5

        if denominator == 0:
            return 0.0

        return numerator / denominator

    def generate_evaluation_report(self) -> Dict[str, Any]:
        """
        生成评估报告

        Returns:
            评估报告字典
        """
        samples = self._builder.load_all_samples()

        quality_distribution = {}
        total_score = 0.0

        for sample in samples.values():
            quality = sample.quality_level
            quality_distribution[quality] = quality_distribution.get(quality, 0) + 1
            total_score += sample.expected_score

        avg_score = total_score / len(samples) if samples else 0.0

        return {
            "total_samples": len(samples),
            "average_score": round(avg_score, 2),
            "quality_distribution": quality_distribution
        }
