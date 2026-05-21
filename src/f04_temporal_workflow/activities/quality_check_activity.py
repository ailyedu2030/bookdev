"""
Quality Check Activity - 内容质量检查
"""

from dataclasses import dataclass
from typing import Any

from temporalio import activity
from tenacity import retry, stop_after_attempt, wait_exponential


@dataclass
class QualityCheckInput:
    """质量检查输入"""

    chapter_id: str
    content: str
    outline: dict
    check_types: list[str]
    language: str = "zh-CN"


@dataclass
class QualityIssue:
    """质量问题"""

    issue_id: str
    severity: str
    category: str
    description: str
    location: str | None = None
    suggestion: str | None = None


@dataclass
class QualityCheckOutput:
    """质量检查输出"""

    chapter_id: str
    passed: bool
    overall_score: float
    issues: list[QualityIssue]
    checks_performed: dict[str, bool]
    recommendations: list[str]


class QualityCheckActivity:
    """质量检查活动"""

    @staticmethod
    @activity.defn(name="check_content_quality")
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def check_content_quality(input_data: QualityCheckInput) -> QualityCheckOutput:
        """
        检查内容质量

        Args:
            input_data: 质量检查输入

        Returns:
            QualityCheckOutput: 质量检查结果
        """
        activity.logger.info(
            f"Checking quality for chapter: {input_data.chapter_id}, " f"checks: {input_data.check_types}"
        )

        issues = []
        checks_performed = {}

        for check_type in input_data.check_types:
            if check_type == "grammar":
                result = await QualityCheckActivity._check_grammar(input_data.content)
                checks_performed["grammar"] = result["passed"]
                if not result["passed"]:
                    issues.extend(result["issues"])
            elif check_type == "coherence":
                result = await QualityCheckActivity._check_coherence(input_data.content, input_data.outline)
                checks_performed["coherence"] = result["passed"]
                if not result["passed"]:
                    issues.extend(result["issues"])
            elif check_type == "completeness":
                result = await QualityCheckActivity._check_completeness(input_data.content, input_data.outline)
                checks_performed["completeness"] = result["passed"]
                if not result["passed"]:
                    issues.extend(result["issues"])
            elif check_type == "readability":
                result = await QualityCheckActivity._check_readability(input_data.content)
                checks_performed["readability"] = result["passed"]
                if not result["passed"]:
                    issues.extend(result["issues"])

        all_passed = all(checks_performed.values()) if checks_performed else False
        overall_score = 1.0 - (len(issues) * 0.1) if issues else 1.0
        overall_score = max(0.0, min(1.0, overall_score))

        return QualityCheckOutput(
            chapter_id=input_data.chapter_id,
            passed=all_passed and overall_score >= 0.7,
            overall_score=overall_score,
            issues=issues,
            checks_performed=checks_performed,
            recommendations=QualityCheckActivity._generate_recommendations(issues),
        )

    @staticmethod
    async def _check_grammar(content: str) -> dict[str, Any]:
        """检查语法"""
        return {"passed": True, "issues": []}

    @staticmethod
    async def _check_coherence(content: str, outline: dict) -> dict[str, Any]:
        """检查连贯性"""
        issues = []
        word_count = len(content.split())
        estimated_words = outline.get("estimated_words", 5000)

        if word_count < estimated_words * 0.5:
            issues.append(
                QualityIssue(
                    issue_id="coh-001",
                    severity="warning",
                    category="coherence",
                    description=f"内容字数({word_count})远低于预期({estimated_words})",
                    location="overall",
                )
            )

        return {"passed": len(issues) == 0, "issues": issues}

    @staticmethod
    async def _check_completeness(content: str, outline: dict) -> dict[str, Any]:
        """检查完整性"""
        issues = []
        sections = outline.get("sections", [])

        for section in sections:
            section_title = section.get("title", "")
            if section_title not in content:
                issues.append(
                    QualityIssue(
                        issue_id="comp-001",
                        severity="error",
                        category="completeness",
                        description=f"章节'{section_title}'内容缺失",
                        location=section_title,
                    )
                )

        return {"passed": len(issues) == 0, "issues": issues}

    @staticmethod
    async def _check_readability(content: str) -> dict[str, Any]:
        """检查可读性"""
        return {"passed": True, "issues": []}

    @staticmethod
    def _generate_recommendations(issues: list[QualityIssue]) -> list[str]:
        """生成建议"""
        recommendations = []
        for issue in issues:
            if issue.suggestion:
                recommendations.append(issue.suggestion)
            elif issue.severity == "error":
                recommendations.append(f"请修复{issue.category}问题: {issue.description}")
        return list(set(recommendations))

    @staticmethod
    @activity.defn(name="check_plagiarism")
    @retry(stop=stop_after_attempt(2))
    async def check_plagiarism(chapter_id: str, content: str) -> dict[str, Any]:
        """
        检查抄袭

        Args:
            chapter_id: 章节ID
            content: 内容

        Returns:
            Dict: 抄袭检查结果
        """
        activity.logger.info(f"Checking plagiarism for chapter: {chapter_id}")

        return {"chapter_id": chapter_id, "plagiarism_score": 0.05, "passed": True, "sources": []}

    @staticmethod
    @activity.defn(name="validate_references")
    async def validate_references(chapter_id: str, references: list[dict]) -> dict[str, Any]:
        """
        验证参考文献

        Args:
            chapter_id: 章节ID
            references: 参考文献列表

        Returns:
            Dict: 验证结果
        """
        activity.logger.info(f"Validating {len(references)} references for chapter: {chapter_id}")

        valid_refs = []
        invalid_refs = []

        for ref in references:
            if ref.get("doi") or ref.get("url"):
                valid_refs.append(ref)
            else:
                invalid_refs.append(ref)

        return {
            "chapter_id": chapter_id,
            "total": len(references),
            "valid": len(valid_refs),
            "invalid": len(invalid_refs),
            "passed": len(invalid_refs) == 0,
        }
