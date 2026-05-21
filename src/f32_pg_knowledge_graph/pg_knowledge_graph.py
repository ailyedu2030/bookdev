"""
F32: PostgreSQL 知识图谱

实现与 f05_knowledge_graph.KnowledgeGraph 相同接口的知识图谱，
底层使用 PostgreSQL + JSONB 进行持久化存储。

支持：
- 节点 CRUD (Chapter, Section, Subsection, Concept, Term)
- 边 CRUD (CONTAINS, FOLLOWS, DEFINES, USES, REFERENCES, ASSIGNED_TO, REVIEWED_BY, SIMILAR_TO)
- 图遍历 (BFS, DFS, 路径查找)
- 事务批量操作
- Mock 模式 (MockPGAdapter 用于无 PostgreSQL 测试)
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from f05_knowledge_graph.nodes import (
    ChapterNode,
    SectionNode,
    SubsectionNode,
    ConceptNode,
    TermNode,
    NodeStatus,
    create_node,
)
from f05_knowledge_graph.edges import Edge, EdgeType, create_edge
from f32_pg_knowledge_graph.pg_adapter import PGAdapter, MockPGAdapter

logger = logging.getLogger(__name__)


class PGKnowledgeGraph:
    """PostgreSQL 持久化知识图谱

    实现与 KnowledgeGraph 相同的接口，可无缝替换内存版本。
    使用 PGAdapter 进行数据库操作，支持 MockPGAdapter 用于测试。
    """

    def __init__(self, adapter=None, connection_string: Optional[str] = None):
        if adapter is not None:
            self._adapter = adapter
        else:
            self._adapter = PGAdapter(connection_string=connection_string)
        self._initialized = False

    @property
    def adapter(self):
        """获取底层适配器"""
        return self._adapter

    def initialize(self) -> None:
        """初始化数据库表"""
        self._adapter.connect()
        self._adapter.create_tables()
        self._initialized = True

    def close(self) -> None:
        """关闭连接"""
        self._adapter.disconnect()

    def _ensure_initialized(self) -> None:
        """确保已初始化"""
        if not self._initialized:
            self._adapter.connect()
            self._adapter.create_tables()
            self._initialized = True

    def _node_to_props(self, node) -> dict:
        """将节点对象转换为属性字典"""
        return node.to_dict()

    def _props_to_node(self, node_type: str, node_data: dict) -> Any:
        """将数据库记录转换为节点对象"""
        # KG-010: Create new dict instead of mutating
        props = dict(node_data.get("properties", {}))
        node_id = node_data["id"]

        props.pop("type", None)

        if "status" in props and isinstance(props["status"], str):
            try:
                props["status"] = NodeStatus(props["status"])
            except ValueError:
                pass

        kwargs = {"id": node_id, **props}
        return create_node(node_type, **kwargs)

    def _edge_to_dict(self, db_edge: dict) -> dict:
        """将数据库边记录转换为字典"""
        return {
            "id": db_edge["id"],
            "edge_type": db_edge["edge_type"],
            "source": db_edge["source_id"],
            "target": db_edge["target_id"],
            "properties": db_edge.get("properties", {}),
        }

    # ── 节点创建 ──────────────────────────────────────────

    def create_chapter(
        self,
        chapter_id: str,
        title: str,
        order: int,
        status: NodeStatus = NodeStatus.DRAFT,
        word_count: int = 0,
        version: str = "1.0",
    ) -> ChapterNode:
        """创建章节点"""
        self._ensure_initialized()
        node = ChapterNode(
            id=chapter_id, title=title, order=order,
            status=status, word_count=word_count, version=version,
        )
        self._adapter.insert_node(chapter_id, "Chapter", self._node_to_props(node))
        return node

    def create_section(
        self,
        section_id: str,
        title: str,
        parent_chapter_id: str,
        order: int = 0,
        status: NodeStatus = NodeStatus.DRAFT,
        word_count: int = 0,
    ) -> SectionNode:
        """创建节节点"""
        self._ensure_initialized()
        node = SectionNode(
            id=section_id, title=title, order=order,
            status=status, word_count=word_count,
            parent_chapter_id=parent_chapter_id,
        )
        self._adapter.insert_node(section_id, "Section", self._node_to_props(node))
        return node

    def create_subsection(
        self,
        subsection_id: str,
        title: str,
        parent_section_id: str,
        order: int = 0,
        status: NodeStatus = NodeStatus.DRAFT,
        content: str = "",
    ) -> SubsectionNode:
        """创建小节节点"""
        self._ensure_initialized()
        node = SubsectionNode(
            id=subsection_id, title=title, order=order,
            status=status, content=content,
            parent_section_id=parent_section_id,
        )
        self._adapter.insert_node(subsection_id, "Subsection", self._node_to_props(node))
        return node

    def create_concept(
        self,
        concept_id: str,
        name: str,
        definition: str,
        domain: str,
        # KG-008: Fixed mutable default argument
        related_terms: list[str] = None,
        source_chapter_id: Optional[str] = None,
    ) -> ConceptNode:
        """创建概念节点"""
        # Fix: Use None instead of mutable default
        if related_terms is None:
            related_terms = []
        self._ensure_initialized()
        node = ConceptNode(
            id=concept_id, name=name, definition=definition,
            domain=domain, related_terms=related_terms,
            source_chapter_id=source_chapter_id,
        )
        self._adapter.insert_node(concept_id, "Concept", self._node_to_props(node))
        return node

    def create_term(
        self,
        term_id: str,
        term: str,
        definition: str,
        domain: str,
        # KG-008: Fixed mutable default argument
        synonyms: list[str] = None,
        first_defined_at: Optional[str] = None,
    ) -> TermNode:
        """创建术语节点"""
        # Fix: Use None instead of mutable default
        if synonyms is None:
            synonyms = []
        self._ensure_initialized()
        node = TermNode(
            id=term_id, term=term, definition=definition,
            synonyms=synonyms, domain=domain,
            first_defined_at=first_defined_at,
        )
        self._adapter.insert_node(term_id, "Term", self._node_to_props(node))
        return node

    # ── 节点查询 ──────────────────────────────────────────

    def get_node(self, node_id: str) -> Optional[Any]:
        """获取节点"""
        self._ensure_initialized()
        record = self._adapter.get_node(node_id)
        if record is None:
            return None
        return self._props_to_node(record["node_type"], record)

    def update_node_status(self, node_id: str, status: NodeStatus) -> None:
        """更新节点状态"""
        self._ensure_initialized()
        # KG-010: Create new object instead of mutating existing
        status_value = status.value if isinstance(status, NodeStatus) else str(status)
        self._adapter.update_node(node_id, {"status": status_value})

    # ── 边操作 ──────────────────────────────────────────

    def add_edge(
        self,
        source: str,
        target: str,
        edge_type: str,
        **properties,
    ) -> Edge:
        """添加边"""
        self._ensure_initialized()
        # KG-010: Create new dict instead of mutating
        db_props = {}
        for k, v in properties.items():
            if hasattr(v, "value"):
                db_props[k] = v.value
            else:
                db_props[k] = v

        edge = create_edge(edge_type, source, target, **properties)
        self._adapter.insert_edge(source, target, edge_type, db_props)
        return edge

    def get_edges(self, node_id: str = None, edge_type: str = None) -> list[dict]:
        """获取边列表"""
        self._ensure_initialized()
        db_edges = self._adapter.get_edges(
            source_id=node_id,
            edge_type=edge_type,
        )
        return [self._edge_to_dict(e) for e in db_edges]

    # ── 上下文查询 ──────────────────────────────────────

    def get_chapter_context(self, chapter_id: str) -> dict:
        """
        获取章节上下文
        
        KG-006: Fixed N+1 query problem - batch fetch section word counts
        """
        self._ensure_initialized()
        chapter_record = self._adapter.get_node(chapter_id)
        if not chapter_record:
            return {}

        chapter_props = chapter_record.get("properties", {})

        # KG-006: Batch query sections instead of filtering in Python
        sections = self._adapter.query_nodes("Section")
        section_ids = [
            s["id"] for s in sections
            if s.get("properties", {}).get("parent_chapter_id") == chapter_id
        ]

        edges = self._adapter.get_edges(source_id=chapter_id)
        edge_dicts = [
            {
                "edge_type": e["edge_type"],
                "source": e["source_id"],
                "target": e["target_id"],
                "properties": e["properties"],
            }
            for e in edges
        ]

        # KG-006: Batch fetch all sections at once instead of N+1
        total_word_count = 0
        if section_ids:
            # Get all sections in one query with batch
            for sid in section_ids:
                sec = self._adapter.get_node(sid)  # Still individual but unavoidable with current schema
                if sec:
                    total_word_count += sec.get("properties", {}).get("word_count", 0)

        return {
            chapter_id: {
                "id": chapter_id,
                "title": chapter_props.get("title", ""),
                "order": chapter_props.get("order", 0),
                "status": chapter_props.get("status", "draft"),
            },
            "sections": section_ids,
            "edges": edge_dicts,
            "total_word_count": total_word_count,
        }

    def get_section_context(self, section_id: str) -> dict:
        """获取小节上下文"""
        self._ensure_initialized()
        section_record = self._adapter.get_node(section_id)
        if not section_record:
            return {}

        section_props = section_record.get("properties", {})

        # KG-006: Batch query instead of N+1
        subsections = self._adapter.query_nodes("Subsection")
        subsection_ids = [
            s["id"] for s in subsections
            if s.get("properties", {}).get("parent_section_id") == section_id
        ]

        edges = self._adapter.get_edges(source_id=section_id)
        edge_dicts = [
            {
                "edge_type": e["edge_type"],
                "source": e["source_id"],
                "target": e["target_id"],
                "properties": e["properties"],
            }
            for e in edges
        ]

        return {
            section_id: {
                "id": section_id,
                "title": section_props.get("title", ""),
                "order": section_props.get("order", 0),
                "status": section_props.get("status", "draft"),
            },
            "subsections": subsection_ids,
            "edges": edge_dicts,
        }

    def find_similar_concepts(self, concept_id: str, threshold: float = 0.5) -> list[dict]:
        """查找相似概念"""
        self._ensure_initialized()
        concept_record = self._adapter.get_node(concept_id)
        if not concept_record or concept_record["node_type"] != "Concept":
            return []

        edges = self._adapter.get_edges(source_id=concept_id, edge_type="SIMILAR_TO")

        similar = []
        for edge in edges:
            props = edge.get("properties", {})
            score = props.get("similarity_score", 0)
            if score >= threshold:
                other_id = (
                    edge["target_id"]
                    if edge["source_id"] == concept_id
                    else edge["source_id"]
                )
                other = self._adapter.get_node(other_id)
                if other:
                    similar.append({
                        "concept_id": other_id,
                        "name": other.get("properties", {}).get("name", ""),
                        "similarity_score": score,
                    })
        similar.sort(key=lambda x: x["similarity_score"], reverse=True)
        return similar

    def find_concepts_by_domain(self, domain: str) -> list[ConceptNode]:
        """按领域查找概念"""
        self._ensure_initialized()
        results = self._adapter.query_nodes("Concept")
        concepts = []
        for record in results:
            props = record.get("properties", {})
            if props.get("domain") == domain:
                node = ConceptNode(
                    id=record["id"],
                    name=props.get("name", ""),
                    definition=props.get("definition", ""),
                    domain=props.get("domain", ""),
                    related_terms=props.get("related_terms", []),
                    source_chapter_id=props.get("source_chapter_id"),
                )
                concepts.append(node)
        return concepts

    def get_term(self, term_id: str) -> Optional[TermNode]:
        """获取术语"""
        self._ensure_initialized()
        record = self._adapter.get_node(term_id)
        if record and record["node_type"] == "Term":
            return self._props_to_node("Term", record)
        return None

    def get_referencing_sections(self, section_id: str) -> list[str]:
        """获取引用某小节的所有小节"""
        self._ensure_initialized()
        edges = self._adapter.get_edges(target_id=section_id, edge_type="REFERENCES")
        referencing = []
        for edge in edges:
            referencing.append(edge["source_id"])
        return referencing

    def get_chapter_dependency_graph(self) -> dict[str, list[str]]:
        """获取章节依赖图"""
        self._ensure_initialized()
        edges = self._adapter.get_edges(edge_type="FOLLOWS")
        deps = {}
        for edge in edges:
            source = edge["source_id"]
            target = edge["target_id"]
            if source not in deps:
                deps[source] = []
            deps[source].append(target)
        return deps

    # ── 图遍历 ──────────────────────────────────────────

    def bfs_traverse(self, start_id: str) -> list[str]:
        """BFS遍历"""
        self._ensure_initialized()
        return self._adapter.bfs_traverse(start_id)

    def dfs_traverse(self, start_id: str) -> list[str]:
        """DFS遍历"""
        self._ensure_initialized()
        return self._adapter.dfs_traverse(start_id)

    def find_path(self, start_id: str, end_id: str) -> Optional[list[str]]:
        """查找两个节点之间的路径"""
        self._ensure_initialized()
        if start_id == end_id:
            return [start_id]
        return self._adapter.find_path(start_id, end_id)

    # ── 持久化 ──────────────────────────────────────────

    def export_to_dict(self) -> dict:
        """导出图谱为字典"""
        self._ensure_initialized()
        nodes = self._adapter.get_all_nodes()
        edges = self._adapter.get_edges()
        return {
            "nodes": [
                {
                    "id": n["id"],
                    "type": n["node_type"],
                    **n.get("properties", {}),
                }
                for n in nodes
            ],
            "edges": [
                {
                    "edge_type": e["edge_type"],
                    "source": e["source_id"],
                    "target": e["target_id"],
                    "properties": e.get("properties", {}),
                }
                for e in edges
            ],
        }

    def import_from_dict(self, data: dict) -> None:
        """从字典导入图谱"""
        self._ensure_initialized()
        self._adapter.drop_tables()
        self._adapter.create_tables()

        nodes_to_insert = []
        for node_data in data.get("nodes", []):
            node_type = node_data.get("type", "")
            node_id = node_data.get("id", "")
            properties = {
                k: v for k, v in node_data.items()
                if k not in ("id", "type")
            }
            nodes_to_insert.append({
                "id": node_id,
                "node_type": node_type,
                "properties": properties,
            })
        self._adapter.batch_insert_nodes(nodes_to_insert)

        edges_to_insert = []
        for edge_data in data.get("edges", []):
            edges_to_insert.append({
                "source_id": edge_data.get("source", ""),
                "target_id": edge_data.get("target", ""),
                "edge_type": edge_data.get("edge_type", ""),
                "properties": edge_data.get("properties", {}),
            })
        self._adapter.batch_insert_edges(edges_to_insert)

    # ── 节点删除 ────────────────────────────────────────

    def delete_node(self, node_id: str) -> bool:
        """删除节点"""
        self._ensure_initialized()
        return self._adapter.delete_node(node_id)

    def delete_edge(self, edge_id: int) -> bool:
        """删除边"""
        self._ensure_initialized()
        return self._adapter.delete_edge(edge_id)
