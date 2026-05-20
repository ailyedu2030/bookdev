"""
F30: Golden Dataset系统 - Dataset构建器

构建和管理Golden Dataset
"""

import json
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class GoldenSample:
    """Golden样本"""
    sample_id: str
    quality_level: str
    expected_score: float
    content: Dict[str, Any]
    quality_metrics: Dict[str, float]
    metadata: Dict[str, Any]
    hallucination_markers: List[Dict[str, Any]] = None
    regulation_errors: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.hallucination_markers is None:
            self.hallucination_markers = []
        if self.regulation_errors is None:
            self.regulation_errors = []

    def __getitem__(self, key):
        """支持字典式访问"""
        return getattr(self, key)

    def get(self, key, default=None):
        """支持字典式get访问"""
        return getattr(self, key, default)


class DatasetBuilder:
    """Dataset构建器"""

    def __init__(self, samples_dir: str = None):
        """
        初始化Dataset构建器

        Args:
            samples_dir: 样本文件目录
        """
        self._samples_dir = samples_dir
        self._samples: Dict[str, GoldenSample] = {}

    def load_all_samples(self) -> Dict[str, GoldenSample]:
        """
        加载所有样本

        Returns:
            样本字典 {sample_id: GoldenSample}
        """
        if self._samples_dir is None:
            return self._samples

        for filename in os.listdir(self._samples_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(self._samples_dir, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    sample = self._parse_sample(data)
                    self._samples[sample.sample_id] = sample

        return self._samples

    def _parse_sample(self, data: Dict[str, Any]) -> GoldenSample:
        """解析样本数据"""
        return GoldenSample(
            sample_id=data["sample_id"],
            quality_level=data["quality_level"],
            expected_score=data["expected_score"],
            content=data["content"],
            quality_metrics=data.get("quality_metrics", {}),
            metadata=data.get("metadata", {}),
            hallucination_markers=data.get("hallucination_markers", []),
            regulation_errors=data.get("regulation_errors", [])
        )

    def load_samples_by_quality(self, quality_level: str) -> List[GoldenSample]:
        """
        按质量等级加载样本

        Args:
            quality_level: 质量等级 (high, medium, low, hallucination, regulation_error)

        Returns:
            样本列表
        """
        if not self._samples:
            self.load_all_samples()

        return [
            sample for sample in self._samples.values()
            if sample.quality_level == quality_level
        ]

    def load_samples_by_score_range(
        self,
        min_score: float = 0.0,
        max_score: float = 10.0
    ) -> List[GoldenSample]:
        """
        按分数范围加载样本

        Args:
            min_score: 最低分数
            max_score: 最高分数

        Returns:
            样本列表
        """
        if not self._samples:
            self.load_all_samples()

        return [
            sample for sample in self._samples.values()
            if min_score <= sample.expected_score <= max_score
        ]

    def get_calibration_samples(self) -> List[GoldenSample]:
        """
        获取校准用样本

        Returns:
            校准样本列表
        """
        if not self._samples:
            self.load_all_samples()

        # 返回所有样本作为校准集
        return list(self._samples.values())

    def add_sample(self, sample_data: Dict[str, Any]) -> GoldenSample:
        """
        添加样本到数据集

        Args:
            sample_data: 样本数据字典

        Returns:
            创建的样本
        """
        sample = self._parse_sample(sample_data)
        self._samples[sample.sample_id] = sample
        return sample

    def validate_sample_structure(self, sample_data: Dict[str, Any]) -> bool:
        """
        验证样本结构

        Args:
            sample_data: 样本数据

        Returns:
            是否有效
        """
        required_fields = [
            "sample_id",
            "quality_level",
            "expected_score",
            "content",
            "quality_metrics",
            "metadata"
        ]

        for field in required_fields:
            if field not in sample_data:
                return False

        return True

    def save_sample(self, sample: GoldenSample, filepath: str = None) -> bool:
        """
        保存样本到文件

        Args:
            sample: 样本
            filepath: 文件路径

        Returns:
            是否成功
        """
        if filepath is None and self._samples_dir:
            filepath = os.path.join(
                self._samples_dir,
                f"{sample.sample_id.lower()}.json"
            )

        if filepath is None:
            return False

        data = {
            "sample_id": sample.sample_id,
            "quality_level": sample.quality_level,
            "expected_score": sample.expected_score,
            "content": sample.content,
            "quality_metrics": sample.quality_metrics,
            "metadata": sample.metadata
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return True
