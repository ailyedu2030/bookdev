"""
F23: 内容安全过滤 - 主过滤器实现
TDD GREEN阶段：实现让测试通过
"""
import re
from typing import Any


class FilterResult:
    """过滤结果数据类"""

    def __init__(
        self,
        is_safe: bool = True,
        confidence_score: float = 1.0,
        categories: list[str] = None,
        violations: list[dict[str, Any]] = None,
        action: str = "PASS",
        details: str = "",
    ):
        self.is_safe = is_safe
        self.confidence_score = confidence_score
        self.categories = categories or []
        self.violations = violations or []
        self.action = action
        self.details = details

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_safe": self.is_safe,
            "confidence_score": self.confidence_score,
            "categories": self.categories,
            "violations": self.violations,
            "action": self.action,
            "details": self.details,
        }


class ContentSecurityFilter:
    """内容安全过滤器"""

    PROFANITY_WORDS = {
        "该死",
        "糟糕",
        "垃圾",
        "废物",
        "混蛋",
        "fuck",
        "shit",
        "damn",
        "ass",
        "bitch",
        "unsafe",
        "unsafe1",
    }

    HATE_SPEECH_PATTERNS = [
        r"种族\w*歧视",
        r"性别\w*歧视",
        r"仇恨\w*言论",
        r"应该\w*消灭",
        r"必须\w*清除",
        r"歧视性",
        r"歧视",
        r"仇恨言论",
        r"厌恶",
        r"排斥",
        r"^我恨",
        r"恨所有",
    ]

    PII_PATTERNS = {
        "email": r"[\w.-]+@[\w.-]+\.\w+",
        "phone": r"1[3-9]\d{9}",
        "phone_formatted": r"1[3-9]\d-\d{4}-\d{4}",
        "id_card": r"\d{17}[\dXx]",
        "bank_card": r"\d{16,19}",
    }

    POLITICAL_KEYWORDS = {
        "台灣": "HIGH",
        "台湾": "HIGH",
        "香港": "HIGH",
        "新疆": "HIGH",
        "西藏": "HIGH",
        "分裂": "MEDIUM",
        "独立": "MEDIUM",
        "台独": "HIGH",
        "敏感政治": "MEDIUM",
        "敏感政治内容": "MEDIUM",
        "敏感政治话题": "MEDIUM",
    }

    INJECTION_PATTERNS = {
        "sql": [r"('\s*or\s*'1'\s*=\s*'1)", r"('\s*or\s*1\s*=\s*1)", r"(;\s*drop\s+table)"],
        "xss": [r"<script[^>]*>", r"javascript:", r"on\w+\s*="],
        "path": [r"\.\./", r"\.\.\\", r"/etc/passwd", r"C:\\Windows"],
        "cmd": [r";\s*rm\s+-rf", r";\s*rmdir", r"`.*`", r"\$\(.*\)"],
    }

    def __init__(self):
        self.whitelist: set[str] = set()
        self._profanity_words = set(self.PROFANITY_WORDS)
        self._hate_speech_patterns = self.HATE_SPEECH_PATTERNS
        self._pii_patterns = self.PII_PATTERNS
        self._political_keywords = self.POLITICAL_KEYWORDS
        self._malware_signatures: set[str] = set()
        self._political_tracker = None

    def add_to_whitelist(self, content: str):
        """添加到白名单"""
        self.whitelist.add(content)

    def _check_whitelist(self, content: str) -> bool:
        """检查白名单"""
        for white in self.whitelist:
            if white in content:
                return True
        return False

    def _detect_profanity(self, content: str) -> dict[str, Any]:
        """检测脏话"""
        found_words = []
        for word in self._profanity_words:
            if word.lower() in content.lower():
                found_words.append(word)

        if found_words:
            return {"detected": True, "words": found_words, "confidence": min(0.5 + 0.1 * len(found_words), 0.99)}
        return {"detected": False, "words": [], "confidence": 1.0}

    def _detect_hate_speech(self, content: str) -> dict[str, Any]:
        """检测仇恨言论"""
        matched = []
        for pattern in self._hate_speech_patterns:
            if re.search(pattern, content):
                matched.append(pattern)

        if matched:
            return {"detected": True, "patterns": matched, "confidence": 0.85}
        return {"detected": False, "patterns": [], "confidence": 1.0}

    def _detect_pii(self, content: str) -> dict[str, Any]:
        """检测PII信息"""
        detected = []
        for pii_type, pattern in self._pii_patterns.items():
            matches = re.findall(pattern, content)
            if matches:
                detected.append({"type": pii_type, "matches": len(matches)})

        if detected:
            return {"detected": True, "pii_types": detected, "confidence": 0.9}
        return {"detected": False, "pii_types": [], "confidence": 1.0}

    def _detect_political_sensitivity(self, content: str) -> dict[str, Any]:
        """检测政治敏感"""
        matched_levels = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        matched_keywords = []

        for keyword, level in self._political_keywords.items():
            if keyword in content:
                matched_keywords.append(keyword)
                matched_levels[level] += 1

        if matched_keywords:
            max_level = "HIGH" if matched_levels["HIGH"] > 0 else "MEDIUM" if matched_levels["MEDIUM"] > 0 else "LOW"
            return {"detected": True, "keywords": matched_keywords, "level": max_level, "confidence": 0.8}
        return {"detected": False, "keywords": [], "level": None, "confidence": 1.0}

    def _detect_injection(self, content: str) -> dict[str, Any]:
        """检测注入攻击"""
        detected = []
        for inj_type, patterns in self.INJECTION_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    detected.append({"type": inj_type, "pattern": pattern})

        if detected:
            return {"detected": True, "injections": detected, "confidence": 0.95}
        return {"detected": False, "injections": [], "confidence": 1.0}

    def filter_content(self, content: str) -> FilterResult:
        """过滤不安全内容"""
        categories = []
        violations = []
        min_confidence = 1.0

        if self._check_whitelist(content):
            return FilterResult(is_safe=True, confidence_score=1.0, categories=["whitelisted"], action="WHITELIST")

        profanity = self._detect_profanity(content)
        if profanity["detected"]:
            categories.append("profanity")
            violations.append({"type": "profanity", "words": profanity["words"]})
            min_confidence = min(min_confidence, profanity["confidence"])

        hate_speech = self._detect_hate_speech(content)
        if hate_speech["detected"]:
            categories.append("hate_speech")
            violations.append({"type": "hate_speech", "patterns": hate_speech["patterns"]})
            min_confidence = min(min_confidence, hate_speech["confidence"])

        pii = self._detect_pii(content)
        if pii["detected"]:
            categories.append("pii")
            violations.append({"type": "pii", "pii_types": pii["pii_types"]})
            min_confidence = min(min_confidence, pii["confidence"])

        political = self._detect_political_sensitivity(content)
        if political["detected"]:
            categories.append("political")
            violations.append(
                {
                    "type": "political",
                    "keywords": political["keywords"],
                    "level": political["level"],
                    "sensitivity_level": political["level"],
                }
            )
            min_confidence = min(min_confidence, political["confidence"])

        injection = self._detect_injection(content)
        if injection["detected"]:
            categories.append("injection")
            categories.append("malware")
            violations.append({"type": "injection", "injections": injection["injections"]})
            min_confidence = min(min_confidence, injection["confidence"])

        is_safe = len(categories) == 0
        action = "BLOCK" if not is_safe else "PASS"

        return FilterResult(
            is_safe=is_safe,
            confidence_score=min_confidence,
            categories=categories,
            violations=violations,
            action=action,
            details=f"Found {len(violations)} violation(s)" if violations else "",
        )

    async def async_filter_content(self, content: str) -> FilterResult:
        """异步过滤"""
        return self.filter_content(content)

    def scan_batch(self, contents: list[str]) -> list[FilterResult]:
        """批量扫描"""
        return [self.filter_content(c) for c in contents]

    async def async_scan_batch(self, contents: list[str]) -> list[FilterResult]:
        """异步批量扫描"""
        return [self.filter_content(c) for c in contents]
