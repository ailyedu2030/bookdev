"""
F23: 内容安全过滤 - 脏话检测器
"""
import re
from typing import List, Tuple, Optional


class ProfanityDetector:
    """脏话检测器"""

    PROFANITY_PATTERNS = {
        "该死": 0.6,
        "糟糕": 0.4,
        "混蛋": 0.7,
        "该死": 0.6,
        "废物": 0.5,
        "智障": 0.6,
        "白痴": 0.6,
        "笨蛋": 0.3,
        "丑陋": 0.3,
        "恶心": 0.4,
        "讨厌": 0.2,
        "该死": 0.6,
        "混蛋": 0.7,
        "王八蛋": 0.8,
        "滚蛋": 0.5,
        "杂种": 0.9,
        "畜生": 0.7,
        "禽兽": 0.6,
        "去死": 0.7,
        "不得好死": 0.8,
    }

    ENGLISH_PROFANITY = {
        "fuck": 0.9,
        "shit": 0.7,
        "damn": 0.4,
        "ass": 0.5,
        "bitch": 0.8,
        "bastard": 0.7,
        "dick": 0.6,
        "piss": 0.5,
        "cunt": 0.9,
        "cock": 0.6,
        "crap": 0.4,
        "bugger": 0.3,
    }

    def __init__(self):
        self._patterns = self._compile_patterns()
        self._english_patterns = self._compile_english_patterns()

    def _compile_patterns(self) -> re.Pattern:
        """编译中文脏话正则"""
        words = "|".join(re.escape(w) for w in self.PROFANITY_PATTERNS.keys())
        return re.compile(words)

    def _compile_english_patterns(self) -> re.Pattern:
        """编译英文脏话正则"""
        words = "|".join(re.escape(w) for w in self.ENGLISH_PROFANITY.keys())
        return re.compile(words, re.IGNORECASE)

    def detect(self, content: str) -> List[Tuple[str, float, int]]:
        """检测脏话

        Returns:
            List of (word, severity, position) tuples
        """
        results = []

        for match in self._patterns.finditer(content):
            word = match.group()
            severity = self.PROFANITY_PATTERNS.get(word, 0.5)
            results.append((word, severity, match.start()))

        for match in self._english_patterns.finditer(content):
            word = match.group().lower()
            severity = self.ENGLISH_PROFANITY.get(word, 0.5)
            results.append((word, severity, match.start()))

        return results

    def is_profane(self, content: str) -> bool:
        """是否包含脏话"""
        return len(self.detect(content)) > 0

    def get_max_severity(self, content: str) -> float:
        """获取最高严重度"""
        detections = self.detect(content)
        if not detections:
            return 0.0
        return max(severity for _, severity, _ in detections)
