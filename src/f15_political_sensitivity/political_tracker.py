"""
F15: 政治敏感分析 - 政治敏感追踪器
TDD GREEN阶段：最小实现让测试通过
"""
import threading
from dataclasses import dataclass, field
from enum import Enum


class SensitivityLevel(Enum):
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class TopicAggregation:
    count: int = 0
    levels: list[SensitivityLevel] = field(default_factory=list)
    is_aggregated_risk: bool = False


@dataclass
class CrossTopicAnalysis:
    is_aggregated_risk: bool = False
    topics: list[str] = field(default_factory=list)
    max_sensitivity: SensitivityLevel = SensitivityLevel.NONE


class PoliticalTracker:
    def __init__(self):
        self._lock = threading.RLock()
        self._topics: dict[str, list[SensitivityLevel]] = {}
        self._sensitivity_cache: dict[str, SensitivityLevel] = {}
        self._normalized_topics: dict[str, str] = {}

    def _normalize_topic(self, topic: str) -> str:
        normalizations = {
            '台灣': '台湾',
            '臺灣': '台湾',
        }
        return normalizations.get(topic, topic.strip())

    def track_topic(self, topic: str, sensitivity_level: SensitivityLevel) -> TopicAggregation:
        with self._lock:
            normalized = self._normalize_topic(topic)
            if normalized not in self._topics:
                self._topics[normalized] = []
                self._normalized_topics[topic] = normalized
            self._topics[normalized].append(sensitivity_level)
            self._sensitivity_cache[normalized] = max(
                self._topics[normalized],
                key=lambda x: x.value
            )
            return self.get_topic_aggregation(normalized)

    def check_topic_sensitivity(self, topic: str) -> SensitivityLevel:
        normalized = self._normalize_topic(topic)
        if normalized in self._sensitivity_cache:
            return self._sensitivity_cache[normalized]
        if topic in self._normalized_topics:
            normalized = self._normalized_topics[topic]
            if normalized in self._sensitivity_cache:
                return self._sensitivity_cache[normalized]
        return SensitivityLevel.NONE

    def get_topic_aggregation(self, topic: str) -> TopicAggregation:
        with self._lock:
            normalized = self._normalize_topic(topic)
            if normalized not in self._topics:
                return TopicAggregation()
            levels = self._topics[normalized]
            max_level = max(levels, key=lambda x: x.value) if levels else SensitivityLevel.NONE
            return TopicAggregation(
                count=len(levels),
                levels=levels,
                is_aggregated_risk=max_level.value >= SensitivityLevel.HIGH.value
            )

    def cross_topic_analysis(self, topics: list[str]) -> CrossTopicAnalysis:
        with self._lock:
            max_sensitivity = SensitivityLevel.NONE
            for topic in topics:
                level = self.check_topic_sensitivity(topic)
                if level.value > max_sensitivity.value:
                    max_sensitivity = level
            return CrossTopicAnalysis(
                is_aggregated_risk=max_sensitivity.value >= SensitivityLevel.HIGH.value,
                topics=topics,
                max_sensitivity=max_sensitivity
            )
