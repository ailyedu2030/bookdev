"""
Security Scan Activity - 安全扫描
"""

import re
from dataclasses import dataclass

from temporalio import activity
from tenacity import retry, stop_after_attempt, wait_exponential


@dataclass
class SecurityScanInput:
    """安全扫描输入"""
    chapter_id: str
    content: str
    scan_types: list[str]


@dataclass
class SecurityIssue:
    """安全问题"""
    issue_id: str
    severity: str
    category: str
    description: str
    location: str | None = None
    remediation: str | None = None


@dataclass
class SecurityScanOutput:
    """安全扫描输出"""
    chapter_id: str
    passed: bool
    risk_score: float
    issues: list[SecurityIssue]
    scan_types_performed: dict[str, bool]


class SecurityScanActivity:
    """安全扫描活动"""

    DANGEROUS_PATTERNS = [
        (r"<script[^>]*>", "XSS", "可能的脚本注入"),
        (r"javascript:", "XSS", "JavaScript协议"),
        (r"on\w+\s*=", "XSS", "内联事件处理器"),
        (r"eval\s*\(", "Code Injection", "eval使用"),
        (r"exec\s*\(", "Code Injection", "exec使用"),
        (r"__import__\s*\(", "Code Injection", "动态导入"),
        (r"subprocess\s*\(", "Command Injection", "子进程调用"),
    ]

    SENSITIVE_PATTERNS = [
        (r"password\s*=\s*['\"][^'\"]+['\"]", "Credentials", "硬编码密码"),
        (r"api[_-]?key\s*=\s*['\"][^'\"]+['\"]", "Credentials", "硬编码API密钥"),
        (r"secret\s*=\s*['\"][^'\"]+['\"]", "Credentials", "硬编码密钥"),
        (r"token\s*=\s*['\"][^'\"]+['\"]", "Credentials", "硬编码Token"),
    ]

    @staticmethod
    @activity.defn(name="scan_security")
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    async def scan_security(input_data: SecurityScanInput) -> SecurityScanOutput:
        """
        执行安全扫描

        Args:
            input_data: 安全扫描输入

        Returns:
            SecurityScanOutput: 扫描结果
        """
        activity.logger.info(
            f"Scanning security for chapter: {input_data.chapter_id}, "
            f"types: {input_data.scan_types}"
        )

        issues = []
        scan_types_performed = {}

        for scan_type in input_data.scan_types:
            if scan_type == "xss":
                result = await SecurityScanActivity._scan_xss(input_data.content)
                scan_types_performed["xss"] = True
                issues.extend(result)
            elif scan_type == "injection":
                result = await SecurityScanActivity._scan_injection(input_data.content)
                scan_types_performed["injection"] = True
                issues.extend(result)
            elif scan_type == "credentials":
                result = await SecurityScanActivity._scan_credentials(input_data.content)
                scan_types_performed["credentials"] = True
                issues.extend(result)
            elif scan_type == "pII":
                result = await SecurityScanActivity._scan_pii(input_data.content)
                scan_types_performed["pII"] = True
                issues.extend(result)

        high_severity_count = sum(1 for i in issues if i.severity == "critical")
        risk_score = min(1.0, (high_severity_count * 0.3) + (len(issues) * 0.05))

        return SecurityScanOutput(
            chapter_id=input_data.chapter_id,
            passed=len([i for i in issues if i.severity == "critical"]) == 0,
            risk_score=risk_score,
            issues=issues,
            scan_types_performed=scan_types_performed
        )

    @staticmethod
    async def _scan_xss(content: str) -> list[SecurityIssue]:
        """扫描XSS"""
        issues = []
        for pattern, category, description in SecurityScanActivity.DANGEROUS_PATTERNS[:3]:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_num = content[:match.start()].count("\n") + 1
                issues.append(SecurityIssue(
                    issue_id=f"xss-{len(issues)+1:03d}",
                    severity="critical",
                    category=category,
                    description=f"发现{description}",
                    location=f"line {line_num}",
                    remediation="请移除或转义此内容"
                ))
        return issues

    @staticmethod
    async def _scan_injection(content: str) -> list[SecurityIssue]:
        """扫描注入"""
        issues = []
        for pattern, category, description in SecurityScanActivity.DANGEROUS_PATTERNS[2:]:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_num = content[:match.start()].count("\n") + 1
                issues.append(SecurityIssue(
                    issue_id=f"inj-{len(issues)+1:03d}",
                    severity="high",
                    category=category,
                    description=f"发现{description}",
                    location=f"line {line_num}",
                    remediation="避免使用动态代码执行"
                ))
        return issues

    @staticmethod
    async def _scan_credentials(content: str) -> list[SecurityIssue]:
        """扫描敏感凭证"""
        issues = []
        for pattern, category, description in SecurityScanActivity.SENSITIVE_PATTERNS:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_num = content[:match.start()].count("\n") + 1
                issues.append(SecurityIssue(
                    issue_id=f"cred-{len(issues)+1:03d}",
                    severity="critical",
                    category=category,
                    description=f"发现{description}",
                    location=f"line {line_num}",
                    remediation="使用环境变量替代硬编码凭证"
                ))
        return issues

    @staticmethod
    async def _scan_pii(content: str) -> list[SecurityIssue]:
        """扫描个人身份信息"""
        issues = []
        pii_patterns = [
            (r"\b\d{15,18}\b", "ID Card", "身份证号"),
            (r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", "Bank Card", "银行卡号"),
            (r"\b\d{3}[-\s]?\d{3}[-\s]?\d{4}\b", "Phone", "电话号码"),
        ]

        for pattern, _category, description in pii_patterns:
            matches = re.finditer(pattern, content)
            if matches:
                issues.append(SecurityIssue(
                    issue_id=f"pii-{len(issues)+1:03d}",
                    severity="medium",
                    category="PII",
                    description=f"可能的{description}模式",
                    remediation="移除或脱敏个人身份信息"
                ))
                break

        return issues

    @staticmethod
    @activity.defn(name="sanitize_content")
    async def sanitize_content(chapter_id: str, content: str) -> str:
        """
        清理内容中的不安全内容

        Args:
            chapter_id: 章节ID
            content: 原始内容

        Returns:
            str: 清理后的内容
        """
        activity.logger.info(f"Sanitizing content for chapter: {chapter_id}")

        sanitized = content

        for pattern, _, _ in SecurityScanActivity.DANGEROUS_PATTERNS:
            sanitized = re.sub(pattern, "[removed]", sanitized, flags=re.IGNORECASE)

        return sanitized
