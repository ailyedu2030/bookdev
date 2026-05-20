"""
F18: 术语一致性检查器

检查术语定义的一致性，检测冲突
"""

from enum import Enum
from typing import Optional

from f18_term_glossary.term_glossary_service import TermGlossaryService


class ConsistencyStatus(Enum):
    CONSISTENT = "consistent"
    INCONSISTENT = "inconsistent"
    UNDEFINED = "undefined"


class ConsistencyChecker:
    """一致性检查器"""

    def __init__(self, glossary: TermGlossaryService):
        self.glossary = glossary
        self._definition_history: dict[str, list[str]] = {}

    def check_consistency(
        self,
        term_name: str,
        new_definition: Optional[str] = None
    ) -> ConsistencyStatus:
        """检查术语一致性

        Args:
            term_name: 术语名称
            new_definition: 新定义 (用于检查是否一致)

        Returns:
            ConsistencyStatus
        """
        term = self.glossary.find_term(term_name)

        if term is None:
            return ConsistencyStatus.UNDEFINED

        if new_definition is None:
            return ConsistencyStatus.CONSISTENT

        if term.definition == new_definition:
            return ConsistencyStatus.CONSISTENT

        return ConsistencyStatus.INCONSISTENT

    def check_all_terms(self) -> dict:
        """检查所有术语的一致性

        Returns:
            一致性报告
        """
        terms = self.glossary.get_all_terms()
        consistent_count = 0
        inconsistent_count = 0
        undefined_count = 0

        for term in terms:
            status = self.check_consistency(term.term)
            if status == ConsistencyStatus.CONSISTENT:
                consistent_count += 1
            elif status == ConsistencyStatus.INCONSISTENT:
                inconsistent_count += 1
            else:
                undefined_count += 1

        return {
            "total_terms": len(terms),
            "consistent_count": consistent_count,
            "inconsistent_count": inconsistent_count,
            "undefined_count": undefined_count,
        }

    def detect_conflicts(self, term_definitions: list[dict]) -> list[dict]:
        """检测术语定义冲突

        Args:
            term_definitions: [{"term": "术语名", "definition": "定义"}, ...]

        Returns:
            冲突列表
        """
        conflicts = []
        term_definitions_map: dict[str, list[str]] = {}

        for item in term_definitions:
            term_name = item["term"]
            definition = item["definition"]

            if term_name not in term_definitions_map:
                term_definitions_map[term_name] = []
            term_definitions_map[term_name].append(definition)

        for term_name, definitions in term_definitions_map.items():
            unique_definitions = set(definitions)
            if len(unique_definitions) > 1:
                conflicts.append({
                    "term": term_name,
                    "definitions": list(unique_definitions),
                    "count": len(unique_definitions),
                })

        return conflicts

    def check_domain_consistency(self, domain: str) -> dict:
        """检查特定领域内术语的一致性

        Args:
            domain: 领域名称

        Returns:
            领域一致性报告
        """
        terms = self.glossary.get_terms_by_domain(domain)

        inconsistencies = []
        for term in terms:
            status = self.check_consistency(term.term)
            if status == ConsistencyStatus.INCONSISTENT:
                inconsistencies.append({
                    "term_id": term.id,
                    "term": term.term,
                    "definition": term.definition,
                })

        return {
            "domain": domain,
            "total_terms": len(terms),
            "inconsistencies": inconsistencies,
            "is_consistent": len(inconsistencies) == 0,
        }

    def get_consistency_report(self) -> dict:
        """生成完整的术语一致性报告

        Returns:
            一致性报告
        """
        all_check = self.check_all_terms()
        terms = self.glossary.get_all_terms()

        by_domain = {}
        for term in terms:
            if term.domain not in by_domain:
                by_domain[term.domain] = []
            by_domain[term.domain].append(term.term)

        return {
            "summary": all_check,
            "by_domain": {
                domain: {
                    "term_count": len(term_names),
                    "terms": term_names,
                }
                for domain, term_names in by_domain.items()
            },
        }
