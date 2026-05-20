"""
F14: 引用完整性校验
引用注册表和完整性管理
"""
import hashlib
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any
from datetime import datetime, timezone
from enum import Enum


@dataclass
class Citation:
    citation_id: str
    doi: str
    fact_hash: str
    position: Dict[str, Any]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_verified: bool = False


@dataclass
class CitationIntegrityResult:
    is_valid: bool
    doi: str
    fact_hash: str
    content_hash: str
    mismatch_reason: Optional[str] = None


@dataclass
class CitationChainResult:
    is_valid: bool
    chain: List[str]
    is_biased: bool = False
    issues: List[str] = field(default_factory=list)


class CitationRegistry:
    """引用注册表"""

    def __init__(self):
        self._citations: Dict[str, Citation] = {}
        self._doi_index: Dict[str, List[str]] = {}
        self._fact_index: Dict[str, List[str]] = {}

    def register_citation(
        self,
        doi: str,
        fact_hash: str,
        position: Dict[str, Any]
    ) -> str:
        """注册引用"""
        existing = self._find_existing_citation(doi, fact_hash, position)
        if existing:
            return existing

        citation_id = str(uuid.uuid4())

        citation = Citation(
            citation_id=citation_id,
            doi=doi,
            fact_hash=fact_hash,
            position=position,
            is_verified=False
        )

        self._citations[citation_id] = citation

        if doi not in self._doi_index:
            self._doi_index[doi] = []
        self._doi_index[doi].append(citation_id)

        if fact_hash not in self._fact_index:
            self._fact_index[fact_hash] = []
        self._fact_index[fact_hash].append(citation_id)

        return citation_id

    def _find_existing_citation(
        self,
        doi: str,
        fact_hash: str,
        position: Dict[str, Any]
    ) -> Optional[str]:
        """查找已存在的引用"""
        citation_ids = self._doi_index.get(doi, [])
        for cid in citation_ids:
            citation = self._citations.get(cid)
            if citation and citation.fact_hash == fact_hash:
                return cid
        return None

    def get_citation(self, citation_id: str) -> Optional[Citation]:
        """获取引用"""
        return self._citations.get(citation_id)

    def list_citations_by_doi(self, doi: str) -> List[Citation]:
        """按DOI列出引用"""
        citation_ids = self._doi_index.get(doi, [])
        return [self._citations[cid] for cid in citation_ids if cid in self._citations]

    def get_fact_citations(self, fact_hash: str) -> List[Citation]:
        """获取引用特定事实的所有引用"""
        citation_ids = self._fact_index.get(fact_hash, [])
        return [self._citations[cid] for cid in citation_ids if cid in self._citations]

    def mark_citation_verified(self, citation_id: str) -> bool:
        """标记引用已验证"""
        if citation_id not in self._citations:
            return False
        self._citations[citation_id].is_verified = True
        return True

    def get_unverified_citations(self) -> List[Citation]:
        """获取所有未验证的引用"""
        return [c for c in self._citations.values() if not c.is_verified]

    def count_citations(self) -> int:
        """获取引用总数"""
        return len(self._citations)

    def count_verified_citations(self) -> int:
        """获取已验证引用数"""
        return sum(1 for c in self._citations.values() if c.is_verified)
