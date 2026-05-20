"""
F05: 图查询引擎

提供高级图查询功能，包括:
- 模式匹配
- 聚合查询
- 子图查询
"""

from typing import Any, Callable, Optional
from collections import defaultdict


class QueryEngine:
    """图查询引擎"""

    def __init__(self, knowledge_graph):
        self.kg = knowledge_graph

    def match_nodes(
        self,
        node_type: str = None,
        predicate: Callable[[Any], bool] = None,
    ) -> list[Any]:
        """模式匹配节点"""
        results = []
        for node in self.kg._nodes.values():
            if node_type and node.type != node_type:
                continue
            if predicate and not predicate(node):
                continue
            results.append(node)
        return results

    def match_edges(
        self,
        edge_type: str = None,
        source_predicate: Callable[[str], bool] = None,
        target_predicate: Callable[[str], bool] = None,
    ) -> list[Any]:
        """模式匹配边"""
        results = []
        for edge in self.kg._edges:
            if edge_type and edge.edge_type != edge_type:
                continue
            if source_predicate and not source_predicate(edge.source):
                continue
            if target_predicate and not target_predicate(edge.target):
                continue
            results.append(edge)
        return results

    def aggregate_by_type(self) -> dict[str, int]:
        """按类型聚合节点"""
        counts = defaultdict(int)
        for node in self.kg._nodes.values():
            counts[node.type] += 1
        return dict(counts)

    def get_subgraph(self, node_ids: list[str]) -> dict:
        """获取子图 (包含指定节点及其关联)"""
        subgraph_nodes = {}
        subgraph_edges = []

        for node_id in node_ids:
            node = self.kg.get_node(node_id)
            if node:
                subgraph_nodes[node_id] = node

        for edge in self.kg._edges:
            if edge.source in subgraph_nodes and edge.target in subgraph_nodes:
                subgraph_edges.append(edge)

        return {
            "nodes": subgraph_nodes,
            "edges": subgraph_edges,
        }

    def find_cliques(self, min_size: int = 3) -> list[list[str]]:
        """查找全连通子图 (cliques) - 简化实现"""
        concept_ids = [
            node_id for node_id, node in self.kg._nodes.items()
            if node.type == "Concept"
        ]

        similar_edges = {
            (e.source, e.target): e.properties.get("similarity_score", 1.0)
            for e in self.kg._edges
            if e.edge_type == "SIMILAR_TO"
        }

        cliques = []
        for i, c1 in enumerate(concept_ids):
            for c2 in concept_ids[i + 1:]:
                if (c1, c2) in similar_edges or (c2, c1) in similar_edges:
                    cliques.append([c1, c2])

        return [c for c in cliques if len(c) >= min_size]

    def get_statistics(self) -> dict[str, Any]:
        """获取图谱统计信息"""
        node_counts = self.aggregate_by_type()
        edge_counts = defaultdict(int)
        for edge in self.kg._edges:
            edge_counts[edge.edge_type] += 1

        return {
            "total_nodes": len(self.kg._nodes),
            "total_edges": len(self.kg._edges),
            "nodes_by_type": node_counts,
            "edges_by_type": dict(edge_counts),
        }
