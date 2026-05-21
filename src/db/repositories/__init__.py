"""
Repository 模块初始化

提供所有 Repository 类的统一导出。
"""

from db.repositories.audit_log_repository import AuditLogRepository
from db.repositories.base_repository import BaseRepository
from db.repositories.chapter_repository import ChapterRepository
from db.repositories.knowledge_graph_repository import KnowledgeGraphRepository
from db.repositories.project_repository import ProjectRepository
from db.repositories.term_repository import TermRepository
from db.repositories.user_repository import UserRepository

__all__ = [
    "BaseRepository",
    "ChapterRepository",
    "ProjectRepository",
    "UserRepository",
    "TermRepository",
    "AuditLogRepository",
    "KnowledgeGraphRepository",
]
