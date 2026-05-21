"""
F15: 政治敏感分析 - 情感分析器
TDD GREEN阶段：最小实现让测试通过
"""
import re
import time
from dataclasses import dataclass
from enum import Enum


class Sentiment(Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


@dataclass
class SentimentResult:
    sentiment: Sentiment
    intensity: float
    is_polarized: bool
    processing_time: float


class SentimentAnalyzer:
    POSITIVE_KEYWORDS = ["好", "棒", "优秀", "出色", "良好", "正面", "促进", "增长", "发展", "正确"]
    NEGATIVE_KEYWORDS = ["问题", "严重", "后果", "垃圾", "愚蠢", "腐败", "无能", "破坏", "负面", "失败"]
    INTENSITY_WORDS = ["非常", "极其", "十分", "特别", "相当", "完全", "彻底"]

    def _calculate_intensity(self, text: str) -> float:
        intensity = 0.5
        for word in self.INTENSITY_WORDS:
            if word in text:
                intensity += 0.1
        repeat_pattern = re.findall(r"(.)\1{2,}", text)
        if repeat_pattern:
            intensity += 0.2
        return min(intensity, 1.0)

    def _is_polarized(self, text: str, sentiment: Sentiment) -> bool:
        if sentiment == Sentiment.NEUTRAL:
            return False
        exclamations = text.count("！") + text.count("!")
        question_marks = text.count("？") + text.count("?")
        all_caps = len(re.findall(r"[A-Z]{3,}", text)) > 0
        if exclamations >= 2 or question_marks >= 2 or all_caps:
            return True
        if len(text) < 20 and (exclamations >= 1 or question_marks >= 1):
            return True
        repeat_pattern = re.findall(r"(.)\1{2,}", text)
        if repeat_pattern:
            return True
        return False

    def analyze(self, content: str) -> SentimentResult:
        start_time = time.time()
        if len(content) > 5000:
            content = content[:5000]
        positive_count = sum(1 for word in self.POSITIVE_KEYWORDS if word in content)
        negative_count = sum(1 for word in self.NEGATIVE_KEYWORDS if word in content)
        if positive_count > negative_count:
            sentiment = Sentiment.POSITIVE
        elif negative_count > positive_count:
            sentiment = Sentiment.NEGATIVE
        else:
            sentiment = Sentiment.NEUTRAL
        intensity = self._calculate_intensity(content)
        is_polarized = self._is_polarized(content, sentiment)
        processing_time = time.time() - start_time
        return SentimentResult(
            sentiment=sentiment, intensity=intensity, is_polarized=is_polarized, processing_time=processing_time
        )
