"""
F15: 政治敏感分析 - 渗透检测器
TDD GREEN阶段：最小实现让测试通过
"""
import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class ThreatType(Enum):
    SAFE = "safe"
    PROPAGANDA = "propaganda"
    DISINFORMATION = "disinformation"
    SUBVERSION = "subversion"
    HATE_SPEECH = "hate_speech"
    COORDINATED_BEHAVIOR = "coordinated_behavior"


@dataclass
class DetectionResult:
    threat_type: ThreatType
    is_safe: bool
    confidence: float
    matched_patterns: List[str]


class InfiltrationDetector:
    PROPAGANDA_PATTERNS = [
        r'必须支持.*党',
        r'唯一正确',
        r'伟大.*领袖',
        r'绝对.*服从',
    ]

    DISINFORMATION_PATTERNS = [
        r'内幕消息',
        r'官方.*伪造',
        r'都是.*骗',
        r'真相是.*掩盖',
    ]

    SUBVERSION_PATTERNS = [
        r'推翻',
        r'打倒',
        r'腐败无能',
        r'必须.*制度',
    ]

    HATE_SPEECH_PATTERNS = [
        r'仇恨',
        r'歧视',
        r'攻击',
    ]

    def _match_patterns(self, content: str, patterns: List[str]) -> List[str]:
        matched = []
        for pattern in patterns:
            if re.search(pattern, content):
                matched.append(pattern)
        return matched

    def detect(self, content: str) -> DetectionResult:
        propaganda = self._match_patterns(content, self.PROPAGANDA_PATTERNS)
        if propaganda:
            return DetectionResult(
                threat_type=ThreatType.PROPAGANDA,
                is_safe=False,
                confidence=0.9,
                matched_patterns=propaganda
            )
        disinfo = self._match_patterns(content, self.DISINFORMATION_PATTERNS)
        if disinfo:
            return DetectionResult(
                threat_type=ThreatType.DISINFORMATION,
                is_safe=False,
                confidence=0.85,
                matched_patterns=disinfo
            )
        subversion = self._match_patterns(content, self.SUBVERSION_PATTERNS)
        if subversion:
            return DetectionResult(
                threat_type=ThreatType.SUBVERSION,
                is_safe=False,
                confidence=0.8,
                matched_patterns=subversion
            )
        hate = self._match_patterns(content, self.HATE_SPEECH_PATTERNS)
        if hate:
            return DetectionResult(
                threat_type=ThreatType.HATE_SPEECH,
                is_safe=False,
                confidence=0.75,
                matched_patterns=hate
            )
        spaced_pattern = re.findall(r'(?:\w\s+){3,}\w', content)
        if spaced_pattern:
            evasion_score = len(spaced_pattern) / max(len(content), 1) * 10
            if evasion_score > 0.5:
                return DetectionResult(
                    threat_type=ThreatType.DISINFORMATION,
                    is_safe=False,
                    confidence=0.6,
                    matched_patterns=["spaced_evasion"]
                )
        return DetectionResult(
            threat_type=ThreatType.SAFE,
            is_safe=True,
            confidence=1.0,
            matched_patterns=[]
        )

    def detect_coordinated_behavior(self, accounts: List[str]) -> Optional[DetectionResult]:
        if len(accounts) >= 3:
            unique_accounts = set(accounts)
            if len(unique_accounts) < len(accounts) * 0.5:
                return DetectionResult(
                    threat_type=ThreatType.COORDINATED_BEHAVIOR,
                    is_safe=False,
                    confidence=0.7,
                    matched_patterns=["coordinated_accounts"]
                )
        return DetectionResult(
            threat_type=ThreatType.SAFE,
            is_safe=True,
            confidence=1.0,
            matched_patterns=[]
        )