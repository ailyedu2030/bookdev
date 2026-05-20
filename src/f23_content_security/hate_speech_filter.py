"""
F23: 内容安全过滤 - 仇恨言论过滤器
"""
import re
from typing import List, Tuple


class HateSpeechFilter:
    """仇恨言论过滤器"""

    HATE_PATTERNS = {
        r"我恨.+人": 0.8,
        r"所有.+人都是.+": 0.9,
        r"杀死|杀掉|消灭": 0.9,
        r"滚出?去": 0.4,
        r"低端|劣根": 0.7,
        r"该死": 0.6,
    }

    DISCRIMINATION_KEYWORDS = {
        "歧视": 0.6,
        "排斥": 0.5,
        "种族主义": 0.9,
        "仇恨": 0.7,
        "暴力": 0.8,
    }

    def __init__(self):
        self._patterns = self._compile_patterns()

    def _compile_patterns(self) -> List[Tuple[re.Pattern, float]]:
        """编译仇恨言论正则"""
        compiled = []
        for pattern, severity in self.HATE_PATTERNS.items():
            compiled.append((re.compile(pattern), severity))
        return compiled

    def detect(self, content: str) -> List[Tuple[str, float, int]]:
        """检测仇恨言论

        Returns:
            List of (matched_text, severity, position) tuples
        """
        results = []

        for pattern, base_severity in self._patterns:
            for match in pattern.finditer(content):
                results.append((match.group(), base_severity, match.start()))

        for keyword, severity in self.DISCRIMINATION_KEYWORDS.items():
            if keyword in content:
                pos = content.find(keyword)
                results.append((keyword, severity, pos))

        return results

    def is_hate_speech(self, content: str) -> bool:
        """是否仇恨言论"""
        return len(self.detect(content)) > 0

    def get_max_severity(self, content: str) -> float:
        """获取最高严重度"""
        detections = self.detect(content)
        if not detections:
            return 0.0
        return max(severity for _, severity, _ in detections)
