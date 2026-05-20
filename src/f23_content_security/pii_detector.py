"""
F23: 内容安全过滤 - PII(个人身份信息)检测器
"""
import re
from typing import List, Tuple, Dict


class PIIDetector:
    """PII个人身份信息检测器"""

    PII_PATTERNS: Dict[str, Tuple[re.Pattern, float, str]] = {
        "id_card": (
            re.compile(r"\b\d{17}[\dXx]\b"),
            0.9,
            "身份证号"
        ),
        "phone_cn": (
            re.compile(r"\b1[3-9]\d{9}\b"),
            0.8,
            "手机号"
        ),
        "phone_formatted": (
            re.compile(r"\b\d{3}[-\s]?\d{4}[-\s]?\d{4}\b"),
            0.7,
            "格式化电话"
        ),
        "email": (
            re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
            0.8,
            "邮箱"
        ),
        "bank_card": (
            re.compile(r"\b\d{16,19}\b"),
            0.9,
            "银行卡号"
        ),
        "passport": (
            re.compile(r"\b[A-Z]\d{8,9}\b"),
            0.9,
            "护照号"
        ),
    }

    NAME_KEYWORDS = ["的", "是", "先生", "女士", "小姐"]

    def __init__(self):
        self._patterns = {k: v[0] for k, v in self.PII_PATTERNS.items()}
        self._severities = {k: v[1] for k, v in self.PII_PATTERNS.items()}
        self._descriptions = {k: v[2] for k, v in self.PII_PATTERNS.items()}

    def detect(self, content: str) -> List[Tuple[str, str, float, int]]:
        """检测PII信息

        Returns:
            List of (matched_content, pii_type, severity, position) tuples
        """
        results = []

        for pii_type, pattern in self._patterns.items():
            for match in pattern.finditer(content):
                matched = match.group()
                severity = self._severities[pii_type]
                description = self._descriptions[pii_type]
                results.append((matched, description, severity, match.start()))

        return results

    def detect_with_name(self, content: str) -> List[Tuple[str, str, float, int]]:
        """检测附带姓名的PII"""
        results = self.detect(content)

        name_pattern = re.compile(r"[\u4e00-\u9fa5]{2,4}(?:先生|女士|小姐|的)")
        for match in name_pattern.finditer(content):
            if any(kw in content[max(0, match.start()-10):match.end()+10]
                   for kw in ["身份证", "电话", "手机", "邮箱", "银行"]):
                results.append((match.group(), "姓名+PII", 0.9, match.start()))

        return results

    def has_pii(self, content: str) -> bool:
        """是否包含PII"""
        return len(self.detect(content)) > 0

    def get_max_severity(self, content: str) -> float:
        """获取最高严重度"""
        detections = self.detect(content)
        if not detections:
            return 0.0
        return max(severity for _, _, severity, _ in detections)

    def get_pii_types(self, content: str) -> List[str]:
        """获取检测到的PII类型"""
        detections = self.detect(content)
        return list(set(desc for _, desc, _, _ in detections))
