"""
F16: 统计抽样验证引擎
基于统计学的抽样验证，确保样本代表性
"""
import math
from dataclasses import dataclass
from enum import Enum


class ChapterType(Enum):
    THEORY = "theory"
    PRACTICE = "practice"
    CASE_STUDY = "case_study"
    REVIEW = "review"


@dataclass
class Chapter:
    id: str
    title: str
    chapter_type: ChapterType
    word_count: int
    metadata: dict | None = None


class StatisticalSamplingEngine:
    """基于统计学的抽样验证，确保样本代表性"""

    Z_SCORES = {
        0.90: 1.645,
        0.95: 1.96,
        0.99: 2.576,
    }

    def __init__(self, confidence_level: float = 0.95, margin_of_error: float = 0.05):
        if confidence_level <= 0 or confidence_level > 1:
            raise ValueError("Confidence level must be between 0 and 1 (exclusive of 0)")
        if margin_of_error <= 0 or margin_of_error >= 1:
            raise ValueError("Margin of error must be between 0 and 1")

        self.confidence_level = confidence_level
        self.margin_of_error = margin_of_error

    def calculate_sample_size(self, population_size: int) -> int:
        """根据总体大小计算所需样本量"""
        if population_size <= 0:
            return 0

        if population_size == 1:
            return 1

        z = self.Z_SCORES.get(self.confidence_level, 1.96)
        p = 0.5

        n0 = (z**2 * p * (1 - p)) / (self.margin_of_error**2)

        n = n0 / (1 + (n0 - 1) / population_size)

        return int(math.ceil(n))

    def stratified_sampling(
        self, chapters: list[Chapter], strata: dict[ChapterType, float], proportional: bool = False
    ) -> list[Chapter]:
        """分层抽样，确保每类章节都有代表"""
        if not chapters:
            return []

        if not strata:
            strata = self._default_strata(chapters)

        strata_chapters: dict[ChapterType, list[Chapter]] = {}
        for chapter_type in ChapterType:
            strata_chapters[chapter_type] = []

        for chapter in chapters:
            if chapter.chapter_type in strata_chapters:
                strata_chapters[chapter.chapter_type].append(chapter)

        result: list[Chapter] = []
        total_chapters = len(chapters)

        for chapter_type, target_ratio in strata.items():
            type_chapters = strata_chapters.get(chapter_type, [])

            if proportional:
                target_count = int(math.ceil(len(type_chapters) * target_ratio))
            else:
                target_count = max(1, int(math.ceil(total_chapters * target_ratio)))

            target_count = min(target_count, len(type_chapters))

            result.extend(type_chapters[:target_count])

        return result

    def _default_strata(self, chapters: list[Chapter]) -> dict[ChapterType, float]:
        """生成默认分层比例"""
        type_counts: dict[ChapterType, int] = {}
        for chapter in chapters:
            ct = chapter.chapter_type
            type_counts[ct] = type_counts.get(ct, 0) + 1

        total = len(chapters)
        if total == 0:
            return {}

        return {ct: count / total for ct, count in type_counts.items()}

    def systematic_sampling(self, chapters: list[Chapter], sample_size: int | None = None) -> list[Chapter]:
        """系统抽样"""
        if not chapters:
            return []

        if sample_size is None:
            sample_size = self.calculate_sample_size(len(chapters))

        sample_size = min(sample_size, len(chapters))

        if sample_size == 0:
            return []

        interval = len(chapters) // sample_size

        if interval == 0:
            return chapters[:sample_size]

        result: list[Chapter] = []
        for i in range(sample_size):
            idx = i * interval
            if idx < len(chapters):
                result.append(chapters[idx])

        return result

    def cluster_sampling(self, chapters: list[Chapter], cluster_size: int = 5) -> list[Chapter]:
        """整群抽样"""
        if not chapters or cluster_size <= 0:
            return []

        clusters: list[list[Chapter]] = []
        for i in range(0, len(chapters), cluster_size):
            cluster = chapters[i : i + cluster_size]
            if cluster:
                clusters.append(cluster)

        if not clusters:
            return []

        import random

        random.seed(42)

        selected_clusters = random.sample(clusters, min(2, len(clusters)))

        result: list[Chapter] = []
        for cluster in selected_clusters:
            result.extend(cluster)

        return result
