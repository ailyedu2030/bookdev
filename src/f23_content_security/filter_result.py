"""
F23: 内容安全过滤 - 过滤结果数据结构
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class FilterAction(Enum):
    """过滤动作"""
    PASS = "PASS"
    WARN = "WARN"
    BLOCK = "BLOCK"
    WHITELIST = "WHITELIST"


class ViolationType(Enum):
    """违规类型"""
    PROFANITY = "profanity"
    HATE_SPEECH = "hate_speech"
    PII = "pii"
    POLITICAL = "political"
    MALWARE = "malware"
    INJECTION = "injection"


@dataclass
class Violation:
    """违规记录"""
    type: str
    category: str
    severity: float
    matched_content: str
    position: int = 0
    length: int = 0
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "category": self.category,
            "severity": self.severity,
            "matched_content": self.matched_content,
            "position": self.position,
            "length": self.length,
            "description": self.description
        }


@dataclass
class FilterResult:
    """内容安全过滤结果"""
    is_safe: bool = True
    confidence_score: float = 1.0
    categories: list[str] = field(default_factory=list)
    violations: list[Violation] = field(default_factory=list)
    action: str = FilterAction.PASS.value
    details: str = ""
    processing_time_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_safe": self.is_safe,
            "confidence_score": self.confidence_score,
            "categories": self.categories,
            "violations": [v.to_dict() for v in self.violations],
            "action": self.action,
            "details": self.details,
            "processing_time_ms": self.processing_time_ms
        }

    def add_violation(
        self,
        violation_type: ViolationType,
        matched_content: str,
        severity: float = 0.5,
        description: str = ""
    ):
        """添加违规记录"""
        violation = Violation(
            type=violation_type.value,
            category=violation_type.value,
            severity=severity,
            matched_content=matched_content,
            description=description
        )
        self.violations.append(violation)
        if violation_type.value not in self.categories:
            self.categories.append(violation_type.value)

    def update_safety_status(self):
        """更新安全状态"""
        self.is_safe = len(self.violations) == 0 or self.action == FilterAction.WHITELIST.value

        if self.action == FilterAction.WHITELIST.value:
            self.is_safe = True
            self.confidence_score = 1.0
        elif self.is_safe:
            self.action = FilterAction.PASS.value
            self.confidence_score = 1.0
        else:
            if any(v.severity >= 0.8 for v in self.violations):
                self.action = FilterAction.BLOCK.value
                self.confidence_score = 0.1
            else:
                self.action = FilterAction.WARN.value
                self.confidence_score = 0.5

    @property
    def severity_score(self) -> float:
        """计算整体严重度"""
        if not self.violations:
            return 0.0
        return max(v.severity for v in self.violations)
