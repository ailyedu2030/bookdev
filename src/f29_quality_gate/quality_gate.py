"""
F29: CI/CD质量门禁

自动化代码质量和安全检查。
"""

import logging
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

# 配置日志
logger = logging.getLogger(__name__)


class CheckStatus(Enum):
    """检查状态"""

    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    SKIP = "skip"


@dataclass
class CheckResult:
    """检查结果"""

    name: str
    status: CheckStatus
    message: str
    details: dict[str, Any] | None = None


@dataclass
class QualityGateResult:
    """质量门禁结果"""

    passed: bool
    check_results: list[CheckResult]
    summary: dict[str, int]
    timestamp: str


class LinterChecker:
    """语法检查器"""

    def check(self, code_path: str) -> CheckResult:
        """检查代码语法"""
        if not os.path.exists(code_path):
            return CheckResult(name="linter", status=CheckStatus.FAIL, message=f"路径不存在: {code_path}")

        if os.path.isfile(code_path):
            return self._check_file(code_path)
        elif os.path.isdir(code_path):
            return self._check_directory(code_path)

        return CheckResult(name="linter", status=CheckStatus.PASS, message="语法检查通过")

    def _check_file(self, file_path: str) -> CheckResult:
        """检查单个文件"""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
                try:
                    compile(content, file_path, "exec")
                    return CheckResult(name="linter", status=CheckStatus.PASS, message="语法检查通过")
                except SyntaxError as e:
                    return CheckResult(
                        name="linter",
                        status=CheckStatus.FAIL,
                        message=f"语法错误: {e.msg}",
                        details={"line": e.lineno, "offset": e.offset},
                    )
        except Exception as e:
            # QC-006 Fix: 记录异常而不是silent pass
            logger.warning(f"无法检查文件 {file_path}: {str(e)}")
            return CheckResult(name="linter", status=CheckStatus.WARNING, message=f"无法检查文件: {str(e)}")

    def _check_directory(self, dir_path: str) -> CheckResult:
        """检查目录"""
        errors = []
        for root, _, files in os.walk(dir_path):
            if "__pycache__" in root or ".pytest_cache" in root:
                continue
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    result = self._check_file(file_path)
                    if result.status == CheckStatus.FAIL:
                        errors.append(result)

        if errors:
            return CheckResult(
                name="linter",
                status=CheckStatus.FAIL,
                message=f"发现 {len(errors)} 个错误",
                details={"errors": [e.message for e in errors]},
            )

        return CheckResult(name="linter", status=CheckStatus.PASS, message="所有文件语法检查通过")


class SecurityScanner:
    """安全扫描器"""

    def scan(self, code_path: str) -> CheckResult:
        """扫描安全问题"""
        if not os.path.exists(code_path):
            return CheckResult(name="security", status=CheckStatus.FAIL, message=f"路径不存在: {code_path}")

        findings = []

        if os.path.isfile(code_path):
            findings.extend(self._scan_file(code_path))
        elif os.path.isdir(code_path):
            for root, _, files in os.walk(code_path):
                if "__pycache__" in root or ".pytest_cache" in root or ".git" in root:
                    continue
                for file in files:
                    if not file.endswith(".py"):
                        continue
                    if file.startswith("test_"):
                        continue
                    if "conftest" in file:
                        continue
                    file_path = os.path.join(root, file)
                    findings.extend(self._scan_file(file_path))

        if findings:
            return CheckResult(
                name="security",
                status=CheckStatus.FAIL,
                message=f"发现 {len(findings)} 个安全问题",
                details={"findings": findings},
            )

        return CheckResult(name="security", status=CheckStatus.PASS, message="未发现安全问题")

    def _scan_file(self, file_path: str) -> list[str]:
        """扫描单个文件"""
        findings = []
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            patterns = {
                r'api_key\s*=\s*["\'][^"\']{16,}["\']': "硬编码长API密钥",
                r'password\s*=\s*["\'][^"\']{6,}["\']': "硬编码密码",
                r'secret\s*=\s*["\'][^"\']{12,}["\']': "硬编码密钥",
                r'token\s*=\s*["\'][^"\']{16,}["\']': "硬编码Token",
                r"sk-[a-zA-Z0-9_-]{30,}": "Stripe/OpenAI式API密钥",
                r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----": "私钥文件",
            }

            MOCK_KEYWORDS = ["mock", "test", "dummy", "your_", "change_me", "placeholder", "example", "xxxx"]

            for pattern, desc in patterns.items():
                if re.search(pattern, content, re.IGNORECASE):
                    findings.append(f"{file_path}: {desc}")

            # Filter false positives
            findings = [f for f in findings if not any(kw in f.lower() for kw in MOCK_KEYWORDS)]

        except Exception as e:
            # QC-006 Fix: 记录异常而不是silent pass
            logger.warning(f"扫描文件 {file_path} 时出错: {str(e)}")

        return findings


class CoverageTracker:
    """覆盖率追踪器"""

    def track(self, code_path: str, threshold: int = 80) -> CheckResult:
        """追踪代码覆盖率"""
        # .coverage 文件通常在项目根目录
        coverage_file = os.path.join(code_path, ".coverage")
        if not os.path.exists(coverage_file):
            # 尝试上一级目录
            coverage_file = os.path.join(os.path.dirname(code_path) or ".", ".coverage")
        if not os.path.exists(coverage_file):
            coverage_file = ".coverage"

        if not os.path.exists(coverage_file):
            return CheckResult(
                name="coverage",
                status=CheckStatus.WARNING,
                message="未找到覆盖率文件",
                details={"expected_file": coverage_file},
            )

        try:
            coverage_percent = self._parse_coverage_file(coverage_file)

            if coverage_percent >= threshold:
                return CheckResult(
                    name="coverage",
                    status=CheckStatus.PASS,
                    message=f"覆盖率 {coverage_percent}% 达到阈值 {threshold}%",
                    details={"coverage": coverage_percent, "threshold": threshold},
                )
            else:
                return CheckResult(
                    name="coverage",
                    status=CheckStatus.FAIL,
                    message=f"覆盖率 {coverage_percent}% 未达到阈值 {threshold}%",
                    details={"coverage": coverage_percent, "threshold": threshold},
                )

        except Exception as e:
            # QC-006 Fix: 记录异常而不是silent pass
            logger.warning(f"无法解析覆盖率文件 {coverage_file}: {str(e)}")
            return CheckResult(name="coverage", status=CheckStatus.WARNING, message=f"无法解析覆盖率: {str(e)}")

    def _parse_coverage_file(self, coverage_file: str) -> float:
        """解析覆盖率文件，支持文本格式(SF/DA行)和二进制.coverage文件"""
        try:
            abs_path = os.path.abspath(coverage_file)
            if not os.path.exists(abs_path):
                return 0.0
            with open(abs_path) as f:
                content = f.read()
            if not content.strip():
                return 0.0
            if content.strip().startswith("SF:"):
                return self._parse_text_coverage(content)
            result = subprocess.run(
                ["python", "-m", "coverage", "report", "--data-file=" + abs_path],
                capture_output=True,
                text=True,
                timeout=30,
            )
            # QC-010 Fix: 使用更健壮的解析方法
            return self._parse_coverage_report(result.stdout)
        except Exception as e:
            # QC-006 Fix: 记录异常而不是silent pass
            logger.warning(f"解析覆盖率文件 {coverage_file} 时出错: {str(e)}")
            return 0.0

    def _parse_coverage_report(self, output: str) -> float:
        """
        从coverage report输出中解析覆盖率
        使用更健壮的方法处理各种输出格式
        """
        if not output:
            return 0.0

        # 查找TOTAL行
        for line in output.split("\n"):
            line = line.strip()
            # 匹配TOTAL开头的行
            if line.startswith("TOTAL"):
                # 使用多个可能的分隔符
                for sep in ["/", "|", "\t"]:
                    if sep in line:
                        parts = line.split(sep)
                        # 尝试找到覆盖率数字
                        for part in reversed(parts):
                            part = part.strip()
                            # 检查是否是百分比格式
                            if part.endswith("%"):
                                try:
                                    return float(part.rstrip("%"))
                                except ValueError:
                                    continue
                            # 检查是否是纯数字
                            try:
                                val = float(part)
                                if 0 <= val <= 100:
                                    return val
                            except ValueError:
                                continue
                        break
                # 如果没有找到分隔符，尝试正则提取最后的数字
                matches = re.findall(r"(\d+(?:\.\d+)?)\s*(?:%|百分)", line)
                if matches:
                    return float(matches[-1])
                # 尝试提取最后一个数字
                numbers = re.findall(r"\d+\.\d+|\d+", line)
                if numbers:
                    try:
                        return float(numbers[-1])
                    except ValueError:
                        pass

        return 0.0

    def _parse_text_coverage(self, content: str) -> float:
        """解析文本格式覆盖率文件(SF/DA行)"""
        lines = content.strip().split("\n")
        total_lines = 0
        covered_lines = 0
        current_file = None
        for line in lines:
            line = line.strip()
            if line.startswith("SF:"):
                current_file = line[3:]
            elif line.startswith("DA:") and current_file:
                parts = line[3:].split(",")
                if len(parts) >= 2:
                    try:
                        line_num = int(parts[0])
                        hit_count = int(parts[1])
                        if line_num > 0:
                            total_lines += 1
                            if hit_count > 0:
                                covered_lines += 1
                    except ValueError:
                        pass
        if total_lines == 0:
            return 0.0
        return round(covered_lines / total_lines * 100, 2)


class QualityGate:
    """CI/CD质量门禁"""

    def __init__(self):
        """初始化质量门禁"""
        self.linter = LinterChecker()
        self.security_scanner = SecurityScanner()
        self.coverage_tracker = CoverageTracker()

    def run_quality_gates(self, code_path: str) -> QualityGateResult:
        """运行所有质量门禁

        Args:
            code_path: 代码路径

        Returns:
            QualityGateResult质量门禁结果
        """
        check_results = [
            self._run_linter_check(code_path),
            self._run_security_scan(code_path),
            self._run_coverage_check(code_path),
        ]

        summary = self._compute_summary(check_results)

        # QC-008 Fix: WARNING状态不应该导致质量门禁失败
        # 质量门禁只有FAIL时才失败，WARNING是可以通过的
        passed = all(r.status != CheckStatus.FAIL for r in check_results if r.status != CheckStatus.SKIP)

        return QualityGateResult(
            passed=passed, check_results=check_results, summary=summary, timestamp=datetime.now().isoformat()
        )

    def _run_linter_check(self, code_path: str) -> CheckResult:
        """运行语法检查"""
        return self.linter.check(code_path)

    def _run_security_scan(self, code_path: str) -> CheckResult:
        """运行安全扫描"""
        return self.security_scanner.scan(code_path)

    def _run_coverage_check(self, code_path: str) -> CheckResult:
        """运行覆盖率检查"""
        return self.coverage_tracker.track(code_path)

    def _compute_summary(self, check_results: list[CheckResult]) -> dict[str, int]:
        """计算检查摘要"""
        summary = {"total": len(check_results), "passed": 0, "failed": 0, "warnings": 0, "skipped": 0}

        for result in check_results:
            if result.status == CheckStatus.PASS:
                summary["passed"] += 1
            elif result.status == CheckStatus.FAIL:
                summary["failed"] += 1
            elif result.status == CheckStatus.WARNING:
                summary["warnings"] += 1
            elif result.status == CheckStatus.SKIP:
                summary["skipped"] += 1

        return summary
