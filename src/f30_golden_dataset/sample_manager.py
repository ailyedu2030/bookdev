"""
F30: Golden Dataset系统 - 样本管理器

管理Golden Dataset样本的CRUD操作
"""

import json
import os
from dataclasses import dataclass, fields
from typing import Any


@dataclass
class GoldenSample:
    """Golden样本"""
    sample_id: str
    quality_level: str
    expected_score: float
    content: dict[str, Any]
    quality_metrics: dict[str, float]
    metadata: dict[str, Any]
    hallucination_markers: list[dict[str, Any]] = None
    regulation_errors: list[dict[str, Any]] = None

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

    def copy_with_updates(self, updates: dict[str, Any]) -> "GoldenSample":
        """
        创建样本的副本并应用更新（保持不可变性）

        Args:
            updates: 要更新的字段

        Returns:
            新的GoldenSample实例
        """
        # Get all current field values
        current_values = {f.name: getattr(self, f.name) for f in fields(self)}

        # Apply updates
        for key, value in updates.items():
            if key in current_values:
                current_values[key] = value

        # Return new instance with updated values
        return GoldenSample(**current_values)


class SampleManager:
    """样本管理器"""

    def __init__(self, samples_dir: str = None):
        """
        初始化样本管理器

        Args:
            samples_dir: 样本文件目录
        """
        self._samples_dir = samples_dir
        self._samples: dict[str, GoldenSample] = {}
        if samples_dir:
            self._load_all()

    def _load_all(self):
        """加载所有样本"""
        if not os.path.exists(self._samples_dir):
            return

        for filename in os.listdir(self._samples_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(self._samples_dir, filename)
                with open(filepath, encoding="utf-8") as f:
                    data = json.load(f)
                    sample = self._parse_sample(data)
                    self._samples[sample.sample_id] = sample

    def _parse_sample(self, data: dict[str, Any]) -> GoldenSample:
        """解析样本数据"""
        return GoldenSample(
            sample_id=data["sample_id"],
            quality_level=data["quality_level"],
            expected_score=data["expected_score"],
            content=data.get("content", {}),
            quality_metrics=data.get("quality_metrics", {}),
            metadata=data.get("metadata", {}),
            hallucination_markers=data.get("hallucination_markers", []),
            regulation_errors=data.get("regulation_errors", [])
        )

    def get_sample_by_id(self, sample_id: str) -> GoldenSample | None:
        """
        通过ID获取样本

        Args:
            sample_id: 样本ID

        Returns:
            样本，不存在返回None
        """
        return self._samples.get(sample_id)

    def list_all_sample_ids(self) -> list[str]:
        """
        列出所有样本ID

        Returns:
            样本ID列表
        """
        return list(self._samples.keys())

    def get_hallucination_samples(self) -> list[GoldenSample]:
        """
        获取幻觉样本

        Returns:
            幻觉样本列表
        """
        return [
            sample for sample in self._samples.values()
            if sample.quality_level == "hallucination"
        ]

    def get_regulation_error_samples(self) -> list[GoldenSample]:
        """
        获取法规错误样本

        Returns:
            法规错误样本列表
        """
        return [
            sample for sample in self._samples.values()
            if sample.quality_level == "regulation_error"
        ]

    def update_sample(
        self,
        sample_id: str,
        updates: dict[str, Any]
    ) -> GoldenSample | None:
        """
        更新样本（保持不可变性）

        INF-009: Instead of mutating the sample object directly, we now
        create a new instance with the updates applied.

        Args:
            sample_id: 样本ID
            updates: 更新内容

        Returns:
            更新后的样本
        """
        sample = self._samples.get(sample_id)
        if sample is None:
            return None

        # Create a new sample with updates instead of mutating
        updated_sample = sample.copy_with_updates(updates)
        self._samples[sample_id] = updated_sample

        return updated_sample

    def delete_sample(self, sample_id: str) -> bool:
        """
        删除样本

        Args:
            sample_id: 样本ID

        Returns:
            是否成功
        """
        if sample_id in self._samples:
            del self._samples[sample_id]
            return True
        return False

    def add_sample(self, sample_data: dict[str, Any]) -> GoldenSample:
        """
        添加样本

        Args:
            sample_data: 样本数据

        Returns:
            创建的样本
        """
        sample = self._parse_sample(sample_data)
        self._samples[sample.sample_id] = sample
        return sample
