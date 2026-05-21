"""
F18: 术语表服务模块
"""

from f18_term_glossary.consistency_checker import ConsistencyChecker
from f18_term_glossary.term_glossary_service import TermGlossaryService
from f18_term_glossary.term_registry import TermRegistry

__all__ = [
    "TermGlossaryService",
    "TermRegistry",
    "ConsistencyChecker",
]
