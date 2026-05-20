"""
Format Review Activity - 格式审查
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple
import re

from temporalio import activity
from tenacity import retry, stop_after_attempt, wait_exponential


@dataclass
class FormatCheckInput:
    """格式检查输入"""
    chapter_id: str
    content: str
    format_standard: str = "textbook"
    language: str = "zh-CN"


@dataclass
class FormatIssue:
    """格式问题"""
    issue_id: str
    severity: str
    category: str
    description: str
    location: Optional[str] = None
    expected: Optional[str] = None
    actual: Optional[str] = None


@dataclass
class FormatCheckOutput:
    """格式检查输出"""
    chapter_id: str
    passed: bool
    format_score: float
    issues: List[FormatIssue]
    statistics: Dict[str, Any]


class FormatReviewActivity:
    """格式审查活动"""

    MARKDOWN_HEADING_PATTERN = re.compile(r"^#{1,6}\s+.+$", re.MULTILINE)
    CHINESE_PUNCTUATION_PATTERN = re.compile(r"[^。，、；：？！""''【】（）、·…—]+")
    ENGLISH_PUNCTUATION_PATTERN = re.compile(r"[,;:.?!\"\'()\[\]·-]+")

    @staticmethod
    @activity.defn(name="check_format")
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    async def check_format(input_data: FormatCheckInput) -> FormatCheckOutput:
        """
        检查格式

        Args:
            input_data: 格式检查输入

        Returns:
            FormatCheckOutput: 格式检查结果
        """
        activity.logger.info(
            f"Checking format for chapter: {input_data.chapter_id}, "
            f"standard: {input_data.format_standard}"
        )

        issues = []

        heading_result = await FormatReviewActivity._check_headings(input_data.content)
        issues.extend(heading_result["issues"])

        punctuation_result = await FormatReviewActivity._check_punctuation(input_data.content)
        issues.extend(punctuation_result["issues"])

        structure_result = await FormatReviewActivity._check_structure(input_data.content)
        issues.extend(structure_result["issues"])

        statistics = FormatReviewActivity._calculate_statistics(input_data.content)

        critical_issues = sum(1 for i in issues if i.severity == "critical")
        format_score = 1.0 - (critical_issues * 0.2) - (len(issues) * 0.02)
        format_score = max(0.0, min(1.0, format_score))

        return FormatCheckOutput(
            chapter_id=input_data.chapter_id,
            passed=critical_issues == 0 and format_score >= 0.7,
            format_score=format_score,
            issues=issues,
            statistics=statistics
        )

    @staticmethod
    async def _check_headings(content: str) -> Dict[str, Any]:
        """检查标题格式"""
        issues = []
        headings = FormatReviewActivity.MARKDOWN_HEADING_PATTERN.findall(content)

        if not headings:
            issues.append(FormatIssue(
                issue_id="fmt-001",
                severity="critical",
                category="structure",
                description="文档缺少标题",
                location="document"
            ))
            return {"issues": issues}

        h1_count = sum(1 for h in headings if h.startswith("# "))
        if h1_count == 0:
            issues.append(FormatIssue(
                issue_id="fmt-002",
                severity="critical",
                category="heading",
                description="缺少一级标题",
                location="document"
            ))
        elif h1_count > 1:
            issues.append(FormatIssue(
                issue_id="fmt-003",
                severity="warning",
                category="heading",
                description=f"一级标题过多({h1_count}个)，建议只有一个",
                location="document"
            ))

        for i, heading in enumerate(headings):
            level = len(heading) - len(heading.lstrip("#"))
            if level > 6:
                issues.append(FormatIssue(
                    issue_id=f"fmt-h{i+1:03d}",
                    severity="error",
                    category="heading",
                    description=f"标题级别超过6级",
                    location=heading[:50]
                ))

        return {"issues": issues}

    @staticmethod
    async def _check_punctuation(content: str) -> Dict[str, Any]:
        """检查标点符号"""
        issues = []

        chinese_text = FormatReviewActivity.CHINESE_PUNCTUATION_PATTERN.sub("", content)
        english_text = FormatReviewActivity.ENGLISH_PUNCTUATION_PATTERN.sub("", content)

        chinese_count = len(chinese_text)
        english_count = len(english_text)

        if chinese_count > 0 and english_count > 0:
            issues.append(FormatIssue(
                issue_id="fmt-010",
                severity="warning",
                category="punctuation",
                description="中英文混排，请注意全角/半角标点",
                location="document"
            ))

        return {"issues": issues}

    @staticmethod
    async def _check_structure(content: str) -> Dict[str, Any]:
        """检查文档结构"""
        issues = []

        lines = content.split("\n")
        empty_lines = sum(1 for line in lines if not line.strip())

        if empty_lines < len(lines) * 0.1:
            issues.append(FormatIssue(
                issue_id="fmt-020",
                severity="warning",
                category="structure",
                description="段落间隔不足",
                location="document"
            ))

        return {"issues": issues}

    @staticmethod
    def _calculate_statistics(content: str) -> Dict[str, Any]:
        """计算统计信息"""
        lines = content.split("\n")

        return {
            "total_lines": len(lines),
            "total_characters": len(content),
            "total_words": len(content.split()),
            "total_chinese_chars": sum(1 for c in content if "\u4e00" <= c <= "\u9fff"),
            "total_english_words": sum(1 for w in content.split() if w.isascii()),
            "headings_count": len(FormatReviewActivity.MARKDOWN_HEADING_PATTERN.findall(content)),
            "code_blocks": content.count("```"),
            "images": content.count("![]"),
            "links": content.count("]("),
        }

    @staticmethod
    @activity.defn(name="format_document")
    async def format_document(
        chapter_id: str,
        content: str,
        format_standard: str = "textbook"
    ) -> str:
        """
        格式化文档

        Args:
            chapter_id: 章节ID
            content: 原始内容
            format_standard: 格式标准

        Returns:
            str: 格式化后的内容
        """
        activity.logger.info(f"Formatting document: {chapter_id}")

        formatted = content

        formatted = re.sub(r"\n{3,}", "\n\n", formatted)

        formatted = formatted.strip()

        return formatted

    @staticmethod
    @activity.defn(name="apply_style_template")
    async def apply_style_template(
        chapter_id: str,
        content: str,
        template_name: str = "standard"
    ) -> str:
        """
        应用样式模板

        Args:
            chapter_id: 章节ID
            content: 原始内容
            template_name: 模板名称

        Returns:
            str: 应用样式后的内容
        """
        activity.logger.info(
            f"Applying style template '{template_name}' to chapter: {chapter_id}"
        )

        if template_name == "standard":
            content = re.sub(r"(\w)---(\w)", r"\1——\2", content)
            content = re.sub(r"(\w)-(\w)", r"\1—\2", content)

        return content

    @staticmethod
    @activity.defn(name="generate_table_of_contents")
    async def generate_table_of_contents(
        chapter_id: str,
        content: str,
        max_level: int = 3
    ) -> str:
        """
        生成目录

        Args:
            chapter_id: 章节ID
            content: 内容
            max_level: 最大标题级别

        Returns:
            str: 目录内容
        """
        activity.logger.info(f"Generating TOC for chapter: {chapter_id}")

        headings = []
        for line in content.split("\n"):
            match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                if level <= max_level:
                    headings.append((level, title))

        toc = "# 目录\n\n"
        for level, title in headings:
            indent = "  " * (level - 1)
            anchor = title.lower().replace(" ", "-")
            toc += f"{indent}- [{title}](#{anchor})\n"

        return toc
