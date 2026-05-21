"""
F32: PostgreSQL 知识图谱持久化模块

提供基于 PostgreSQL + JSONB 的知识图谱持久化层，
实现与 f05_knowledge_graph.KnowledgeGraph 相同的接口。
"""

from f32_pg_knowledge_graph.connection_pool import ConnectionPool
from f32_pg_knowledge_graph.pg_adapter import MockPGAdapter, PGAdapter
from f32_pg_knowledge_graph.pg_knowledge_graph import PGKnowledgeGraph

__all__ = [
    "PGKnowledgeGraph",
    "ConnectionPool",
    "PGAdapter",
    "MockPGAdapter",
]
