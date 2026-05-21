"""
F14: 引用完整性校验
引用注册表和完整性管理
"""
from f14_citation_integrity.citation_integrity_manager import (
    CitationChainResult,
    CitationIntegrityManager,
    CitationIntegrityResult,
    FactCollision,
    IntegrityStatus,
)
from f14_citation_integrity.citation_registry import Citation, CitationRegistry

__all__ = [
    "CitationRegistry",
    "Citation",
    "CitationIntegrityManager",
    "CitationIntegrityResult",
    "CitationChainResult",
    "IntegrityStatus",
    "FactCollision",
]
