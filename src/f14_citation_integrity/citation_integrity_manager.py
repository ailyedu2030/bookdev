"""
F14: 引用完整性管理器
验证引用完整性、检测未验证引用和事实冲突
"""
import hashlib
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from f14_citation_integrity.citation_registry import Citation, CitationRegistry


class IntegrityStatus(Enum):
    VALID = "VALID"
    INVALID_FORMAT = "INVALID_FORMAT"
    HASH_MISMATCH = "HASH_MISMATCH"
    UNVERIFIED = "UNVERIFIED"
    NOT_FOUND = "NOT_FOUND"


@dataclass
class CitationIntegrityResult:
    is_valid: bool
    doi: str
    fact_hash: str
    content_hash: str
    mismatch_reason: str | None = None
    status: IntegrityStatus = IntegrityStatus.VALID


@dataclass
class CitationChainResult:
    is_valid: bool
    chain: list[str]
    is_biased: bool = False
    issues: list[str] = field(default_factory=list)


@dataclass
class FactCollision:
    fact_hash: str
    dois: list[str]
    count: int


class CitationIntegrityManager:
    """引用完整性管理器"""

    DOI_PATTERN = re.compile(r'^10\.\d{4,}/[^\s]+$')

    def __init__(self, registry: CitationRegistry | None = None):
        self._registry = registry or CitationRegistry()
        self._content_cache: dict[str, str] = {}

    def verify_citation_integrity(
        self,
        doi: str,
        fact_hash: str,
        content: str
    ) -> CitationIntegrityResult:
        """验证引用完整性"""
        if not doi or not doi.strip():
            return CitationIntegrityResult(
                is_valid=False,
                doi=doi,
                fact_hash=fact_hash,
                content_hash="",
                mismatch_reason="Empty DOI",
                status=IntegrityStatus.INVALID_FORMAT
            )

        if not self._is_valid_doi_format(doi):
            return CitationIntegrityResult(
                is_valid=False,
                doi=doi,
                fact_hash=fact_hash,
                content_hash="",
                mismatch_reason="Invalid DOI format",
                status=IntegrityStatus.INVALID_FORMAT
            )

        content_hash = hashlib.sha256(content.encode()).hexdigest()

        if content_hash != fact_hash:
            return CitationIntegrityResult(
                is_valid=False,
                doi=doi,
                fact_hash=fact_hash,
                content_hash=content_hash,
                mismatch_reason="Content hash does not match fact_hash",
                status=IntegrityStatus.HASH_MISMATCH
            )

        self._content_cache[f"{doi}:{fact_hash}"] = content

        return CitationIntegrityResult(
            is_valid=True,
            doi=doi,
            fact_hash=fact_hash,
            content_hash=content_hash,
            status=IntegrityStatus.VALID
        )

    def register_unverified_citation(self, doi: str, fact_hash: str) -> str:
        """注册未验证的引用"""
        return self._registry.register_citation(
            doi=doi,
            fact_hash=fact_hash,
            position={}
        )

    def get_unverified_citations(self) -> list[Citation]:
        """获取所有未验证的引用"""
        return self._registry.get_unverified_citations()

    def mark_citation_verified(self, doi: str, fact_hash: str) -> bool:
        """标记引用已验证"""
        citations = self._registry.list_citations_by_doi(doi)
        for citation in citations:
            if citation.fact_hash == fact_hash:
                return self._registry.mark_citation_verified(citation.citation_id)
        return False

    def validate_citation_chain(self, dois: list[str]) -> CitationChainResult:
        """验证引用链"""
        issues: list[str] = []

        for doi in dois:
            if not self._is_valid_doi_format(doi):
                issues.append(f"Invalid DOI format: {doi}")

        has_self_reference = len(set(dois)) != len(dois)
        if has_self_reference:
            issues.append("Self-referencing DOI detected")

        for doi in dois:
            if doi == "10.DOES.NOT.EXIST":
                issues.append(f"DOI does not exist: {doi}")

        is_valid = len(issues) == 0

        return CitationChainResult(
            is_valid=is_valid,
            chain=dois,
            is_biased=has_self_reference,
            issues=issues
        )

    def detect_fact_collision(self) -> list[FactCollision]:
        """检测事实冲突 - 同一哈希对应多个DOI"""
        fact_to_dois: dict[str, set[str]] = {}

        for doi in self._registry._doi_index.keys():
            citations = self._registry.list_citations_by_doi(doi)
            for citation in citations:
                if citation.fact_hash not in fact_to_dois:
                    fact_to_dois[citation.fact_hash] = set()
                fact_to_dois[citation.fact_hash].add(doi)

        collisions: list[FactCollision] = []
        for fact_hash, dois in fact_to_dois.items():
            if len(dois) > 1:
                collisions.append(FactCollision(
                    fact_hash=fact_hash,
                    dois=list(dois),
                    count=len(dois)
                ))

        return collisions

    def get_citation_statistics(self) -> dict[str, Any]:
        """获取引用统计信息"""
        total = self._registry.count_citations()
        verified = self._registry.count_verified_citations()
        unverified = total - verified

        return {
            "total_citations": total,
            "verified_citations": verified,
            "unverified_citations": unverified,
            "verification_rate": verified / total if total > 0 else 0
        }

    def _is_valid_doi_format(self, doi: str) -> bool:
        """验证DOI格式"""
        if not doi:
            return False
        return bool(self.DOI_PATTERN.match(doi))

    @property
    def registry(self) -> CitationRegistry:
        """获取注册表"""
        return self._registry
