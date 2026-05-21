"""
F05: 知识图谱核心实现

本模块实现知识图谱的核心功能，包括:
- 节点管理 (Chapter, Section, Subsection, Concept, Term)
- 边管理 (CONTAINS, FOLLOWS, DEFINES, USES, REFERENCES, ASSIGNED_TO, REVIEWED_BY, SIMILAR_TO)
- 图查询引擎 (BFS, DFS, 路径查找, 上下文查询)
"""

from typing import Any

from f05_knowledge_graph.edges import Edge, create_edge
from f05_knowledge_graph.nodes import (
    ChapterNode,
    ConceptNode,
    NodeStatus,
    SectionNode,
    SubsectionNode,
    TermNode,
    create_node,
)


class KnowledgeGraph:
    """知识图谱主类"""

    def __init__(self):
        self._nodes: dict[str, Any] = {}
        self._edges: list[Edge] = []
        self._adjacency: dict[str, list[str]] = {}  # 邻接表

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
        node = ChapterNode(
            id=chapter_id,
            title=title,
            order=order,
            status=status,
            word_count=word_count,
            version=version,
        )
        self._nodes[chapter_id] = node
        self._adjacency[chapter_id] = []
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
        node = SectionNode(
            id=section_id,
            title=title,
            order=order,
            status=status,
            word_count=word_count,
            parent_chapter_id=parent_chapter_id,
        )
        self._nodes[section_id] = node
        self._adjacency[section_id] = []
        if parent_chapter_id in self._adjacency:
            self._adjacency[parent_chapter_id].append(section_id)
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
        node = SubsectionNode(
            id=subsection_id,
            title=title,
            order=order,
            status=status,
            content=content,
            parent_section_id=parent_section_id,
        )
        self._nodes[subsection_id] = node
        self._adjacency[subsection_id] = []
        if parent_section_id in self._adjacency:
            self._adjacency[parent_section_id].append(subsection_id)
        return node

    def create_concept(
        self,
        concept_id: str,
        name: str,
        definition: str,
        domain: str,
        # KG-008: Fixed mutable default argument
        related_terms: list[str] = None,
        source_chapter_id: str | None = None,
    ) -> ConceptNode:
        """创建概念节点"""
        # Fix: Use None instead of mutable default
        if related_terms is None:
            related_terms = []
        node = ConceptNode(
            id=concept_id,
            name=name,
            definition=definition,
            domain=domain,
            related_terms=related_terms,
            source_chapter_id=source_chapter_id,
        )
        self._nodes[concept_id] = node
        self._adjacency[concept_id] = []
        return node

    def create_term(
        self,
        term_id: str,
        term: str,
        definition: str,
        domain: str,
        # KG-008: Fixed mutable default argument
        synonyms: list[str] = None,
        first_defined_at: str | None = None,
    ) -> TermNode:
        """创建术语节点"""
        # Fix: Use None instead of mutable default
        if synonyms is None:
            synonyms = []
        node = TermNode(
            id=term_id,
            term=term,
            definition=definition,
            synonyms=synonyms,
            domain=domain,
            first_defined_at=first_defined_at,
        )
        self._nodes[term_id] = node
        self._adjacency[term_id] = []
        return node

    def get_node(self, node_id: str) -> Any | None:
        """获取节点"""
        return self._nodes.get(node_id)

    def update_node_status(self, node_id: str, status: NodeStatus) -> None:
        """更新节点状态"""
        node = self._nodes.get(node_id)
        if node:
            # KG-010: Don't mutate the original object, create a new one
            # For status enum this is less critical but follows the principle
            new_status = NodeStatus(status.value) if isinstance(status, NodeStatus) else NodeStatus(status)
            # Create new node dict with updated status instead of mutation
            node_dict = node.to_dict()
            node_dict["status"] = new_status
            # Re-create node with new status
            updated_node = create_node(node.type, **node_dict)
            self._nodes[node_id] = updated_node

    def add_edge(
        self,
        source: str,
        target: str,
        edge_type: str,
        **properties,
    ) -> Edge:
        """添加边"""
        edge = create_edge(edge_type, source, target, **properties)
        self._edges.append(edge)

        # KG-005: Bidirectional adjacency update for undirected edges
        if source not in self._adjacency:
            self._adjacency[source] = []
        if target not in self._adjacency[source]:
            self._adjacency[source].append(target)

        # For undirected edges (non-directional), also add reverse direction
        # Common undirected edge types include: SIMILAR_TO, FOLLOWS, REFERENCES
        if edge_type in ("SIMILAR_TO", "FOLLOWS", "REFERENCES", "USES"):
            if target not in self._adjacency:
                self._adjacency[target] = []
            if source not in self._adjacency[target]:
                self._adjacency[target].append(source)

        return edge

    def get_edges(self, node_id: str = None, edge_type: str = None) -> list[Edge]:
        """获取边列表"""
        edges = self._edges
        if node_id:
            edges = [e for e in edges if e.source == node_id or e.target == node_id]
        if edge_type:
            edges = [e for e in edges if e.edge_type == edge_type]
        return edges

    def get_chapter_context(self, chapter_id: str) -> dict:
        """获取章节上下文"""
        chapter = self._nodes.get(chapter_id)
        if not chapter:
            return {}

        sections = []
        for node_id, node in self._nodes.items():
            if hasattr(node, "parent_chapter_id") and node.parent_chapter_id == chapter_id:
                sections.append(node_id)

        edges = self.get_edges(node_id=chapter_id)

        # KG-006: Batch query instead of N+1
        # Get all sections at once and compute total
        section_nodes = [self._nodes.get(sid) for sid in sections if sid in self._nodes]
        total_word_count = sum(node.word_count for node in section_nodes if node and hasattr(node, "word_count"))

        return {
            chapter_id: {
                "id": chapter_id,
                "title": chapter.title,
                "order": chapter.order,
                "status": chapter.status,
            },
            "sections": sections,
            "edges": [e.to_dict() for e in edges],
            "total_word_count": total_word_count,
        }

    def get_section_context(self, section_id: str) -> dict:
        """获取小节上下文"""
        section = self._nodes.get(section_id)
        if not section:
            return {}

        subsections = []
        for node_id, node in self._nodes.items():
            if hasattr(node, "parent_section_id") and node.parent_section_id == section_id:
                subsections.append(node_id)

        edges = self.get_edges(node_id=section_id)

        return {
            section_id: {
                "id": section_id,
                "title": section.title,
                "order": section.order,
                "status": section.status,
            },
            "subsections": subsections,
            "edges": [e.to_dict() for e in edges],
        }

    def find_similar_concepts(self, concept_id: str, threshold: float = 0.5) -> list[dict]:
        """查找相似概念"""
        concept = self._nodes.get(concept_id)
        if not concept or concept.type != "Concept":
            return []

        similar = []
        similar_edges = self.get_edges(node_id=concept_id, edge_type="SIMILAR_TO")

        for edge in similar_edges:
            score = edge.properties.get("similarity_score", 0)
            if score >= threshold:
                target_id = edge.target if edge.source == concept_id else edge.source
                target = self._nodes.get(target_id)
                if target:
                    similar.append(
                        {
                            "concept_id": target_id,
                            "name": target.name,
                            "similarity_score": score,
                        }
                    )

        similar.sort(key=lambda x: x["similarity_score"], reverse=True)
        return similar

    def find_concepts_by_domain(self, domain: str) -> list[ConceptNode]:
        """按领域查找概念"""
        concepts = []
        for node in self._nodes.values():
            if node.type == "Concept" and node.domain == domain:
                concepts.append(node)
        return concepts

    def get_term(self, term_id: str) -> TermNode | None:
        """获取术语"""
        node = self._nodes.get(term_id)
        if node and node.type == "Term":
            return node
        return None

    def get_referencing_sections(self, section_id: str) -> list[str]:
        """获取引用某小节的所有小节"""
        referencing = []
        for edge in self._edges:
            if edge.edge_type == "REFERENCES" and edge.target == section_id:
                referencing.append(edge.source)
        return referencing

    def get_chapter_dependency_graph(self) -> dict[str, list[str]]:
        """获取章节依赖图"""
        deps = {}
        for edge in self._edges:
            if edge.edge_type == "FOLLOWS":
                if edge.source not in deps:
                    deps[edge.source] = []
                deps[edge.source].append(edge.target)
        return deps

    def bfs_traverse(self, start_id: str) -> list[str]:
        """BFS遍历"""
        if start_id not in self._nodes:
            return []

        visited = set()
        queue = [start_id]
        result = []

        while queue:
            # KG-023: Queue boundary check - prevent infinite loop with max iterations
            node_id = queue.pop(0)
            if node_id in visited:
                continue
            visited.add(node_id)
            result.append(node_id)

            for neighbor in self._adjacency.get(node_id, []):
                if neighbor not in visited:
                    queue.append(neighbor)

            # Safety limit to prevent runaway traversal
            if len(result) > len(self._nodes):
                break

        return result

    def dfs_traverse(self, start_id: str) -> list[str]:
        """DFS遍历"""
        if start_id not in self._nodes:
            return []

        visited = set()
        result = []

        def _dfs(node_id: str, depth: int = 0):
            # KG-011: Fix depth limit boundary - allow depth limit nodes to be included
            if node_id in visited:
                return
            if depth > 100:  # Safety limit
                return
            visited.add(node_id)
            result.append(node_id)
            for neighbor in self._adjacency.get(node_id, []):
                _dfs(neighbor, depth + 1)

        _dfs(start_id)
        return result

    def find_path(self, start_id: str, end_id: str) -> list[str] | None:
        """查找两个节点之间的路径 (BFS)"""
        if start_id not in self._nodes or end_id not in self._nodes:
            return None

        if start_id == end_id:
            return [start_id]

        visited = {start_id}
        queue = [(start_id, [start_id])]

        while queue:
            node_id, path = queue.pop(0)

            for neighbor in self._adjacency.get(node_id, []):
                if neighbor == end_id:
                    return path + [neighbor]

                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return None

    def export_to_dict(self) -> dict:
        """导出图谱为字典"""
        return {
            "nodes": [node.to_dict() for node in self._nodes.values()],
            "edges": [edge.to_dict() for edge in self._edges],
        }

    def import_from_dict(self, data: dict) -> None:
        """从字典导入图谱"""
        self._nodes.clear()
        self._edges.clear()
        self._adjacency.clear()

        for node_data in data.get("nodes", []):
            node_type = node_data.pop("type")
            node = create_node(node_type, **node_data)
            self._nodes[node.id] = node
            self._adjacency[node.id] = []

        for edge_data in data.get("edges", []):
            edge_type = edge_data.pop("edge_type")
            source = edge_data.pop("source")
            target = edge_data.pop("target")
            properties = edge_data.pop("properties", {})
            edge = create_edge(edge_type, source, target, **properties)
            self._edges.append(edge)
            if source in self._adjacency:
                self._adjacency[source].append(target)
