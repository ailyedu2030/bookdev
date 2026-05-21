"""
Term Check Activity - 术语检查
"""

from collections import defaultdict
from dataclasses import dataclass

from temporalio import activity
from tenacity import retry, stop_after_attempt, wait_exponential


@dataclass
class TermCheckInput:
    """术语检查输入"""

    chapter_id: str
    content: str
    glossary: dict | None = None
    preferred_terms: dict[str, str] | None = None


@dataclass
class TermIssue:
    """术语问题"""

    issue_id: str
    severity: str
    category: str
    original_term: str
    suggested_term: str | None
    location: str | None = None


@dataclass
class TermCheckOutput:
    """术语检查输出"""

    chapter_id: str
    passed: bool
    consistency_score: float
    issues: list[TermIssue]
    terms_used: set[str]
    glossary_coverage: float


DEFAULT_GLOSSARY = {
    "人工智能": "AI",
    "机器学习": "ML",
    "深度学习": "Deep Learning",
    "神经网络": "Neural Network",
    "自然语言处理": "NLP",
    "计算机视觉": "Computer Vision",
}


class TermCheckActivity:
    """术语检查活动"""

    @staticmethod
    @activity.defn(name="check_term_consistency")
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def check_term_consistency(input_data: TermCheckInput) -> TermCheckOutput:
        """
        检查术语一致性

        Args:
            input_data: 术语检查输入

        Returns:
            TermCheckOutput: 术语检查结果
        """
        activity.logger.info(f"Checking term consistency for chapter: {input_data.chapter_id}")

        glossary = input_data.glossary or DEFAULT_GLOSSARY
        preferred_terms = input_data.preferred_terms or {}

        issues = []
        terms_found = set()

        content_lower = input_data.content.lower()

        for term, preferred in glossary.items():
            term_lower = term.lower()
            preferred_lower = preferred.lower()

            if term_lower in content_lower:
                terms_found.add(term)

            if preferred_lower in content_lower and term_lower in content_lower:
                issues.append(
                    TermIssue(
                        issue_id=f"term-{len(issues)+1:03d}",
                        severity="warning",
                        category="inconsistent",
                        original_term=term,
                        suggested_term=preferred,
                        location="content",
                    )
                )

        for original, replacement in preferred_terms.items():
            if original.lower() in content_lower and replacement.lower() not in content_lower:
                issues.append(
                    TermIssue(
                        issue_id=f"term-{len(issues)+1:03d}",
                        severity="info",
                        category="preferred",
                        original_term=original,
                        suggested_term=replacement,
                        location="content",
                    )
                )

        glossary_terms = set(glossary.keys())
        glossary_coverage = len(terms_found & glossary_terms) / len(glossary_terms) if glossary_terms else 0.0

        inconsistency_count = sum(1 for i in issues if i.category == "inconsistent")
        consistency_score = 1.0 - (inconsistency_count * 0.1)
        consistency_score = max(0.0, min(1.0, consistency_score))

        return TermCheckOutput(
            chapter_id=input_data.chapter_id,
            passed=inconsistency_count == 0,
            consistency_score=consistency_score,
            issues=issues,
            terms_used=terms_found,
            glossary_coverage=glossary_coverage,
        )

    @staticmethod
    @activity.defn(name="normalize_terms")
    async def normalize_terms(chapter_id: str, content: str, term_map: dict[str, str]) -> str:
        """
        标准化术语

        Args:
            chapter_id: 章节ID
            content: 原始内容
            term_map: 术语映射 {原术语: 标准术语}

        Returns:
            str: 标准化后的内容
        """
        activity.logger.info(f"Normalizing terms for chapter: {chapter_id}")

        normalized = content
        for original, standard in term_map.items():
            pattern = rf"\b{re.escape(original)}\b"
            normalized = re.sub(pattern, standard, normalized, flags=re.IGNORECASE)

        return normalized

    @staticmethod
    @activity.defn(name="extract_terms")
    @retry(stop=stop_after_attempt(2))
    async def extract_terms(chapter_id: str, content: str) -> dict[str, list[str]]:
        """
        从内容中提取术语

        Args:
            chapter_id: 章节ID
            content: 内容

        Returns:
            Dict: 提取的术语及其位置
        """
        activity.logger.info(f"Extracting terms from chapter: {chapter_id}")

        term_positions = defaultdict(list)
        term_pattern = r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*"

        for match in re.finditer(term_pattern, content):
            term = match.group()
            line_num = content[: match.start()].count("\n") + 1
            term_positions[term].append(f"line {line_num}")

        return dict(term_positions)

    @staticmethod
    @activity.defn(name="build_chapter_glossary")
    async def build_chapter_glossary(chapter_id: str, terms: dict[str, list[str]]) -> dict:
        """
        为章节构建术语表

        Args:
            chapter_id: 章节ID
            terms: 提取的术语

        Returns:
            dict: 章节术语表
        """
        activity.logger.info(f"Building glossary for chapter: {chapter_id}")

        glossary = {}
        for term, locations in terms.items():
            glossary[term] = {
                "occurrences": len(locations),
                "first_location": locations[0] if locations else None,
                "definition": None,
            }

        return glossary
