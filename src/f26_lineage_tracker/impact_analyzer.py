"""
F26: 血缘追踪系统 - 影响分析器
计算数据变更对下游的影响范围
"""
from typing import List, Set, Dict, Any
from dataclasses import dataclass, field

from lineage_tracker import DataLineageTracker
from lineage_node import LineageNode, ImpactReport


class ImpactAnalyzer:
    """影响分析器"""

    def __init__(self, tracker: DataLineageTracker):
        self.tracker = tracker

    def compute_impact_analysis(self, source_id: str) -> ImpactReport:
        """影响分析：计算哪些下游受影响"""
        node_id = f"node_{source_id}"

        if node_id not in self.tracker._node_index:
            return ImpactReport(
                source_id=source_id,
                affected_nodes=[],
                total_affected=0,
                max_depth=0,
                critical_paths=[]
            )

        affected_nodes: List[str] = []
        max_depth = 0
        critical_paths: List[List[str]] = []

        if node_id not in self.tracker.lineage_graph:
            return ImpactReport(
                source_id=source_id,
                affected_nodes=[],
                total_affected=0,
                max_depth=0,
                critical_paths=[]
            )

        try:
            descendants = nx.descendants(self.tracker.lineage_graph, node_id)

            for desc_id in descendants:
                if desc_id in self.tracker._node_index:
                    node = self.tracker._node_index[desc_id]
                    affected_nodes.append(desc_id)

                    if hasattr(node, 'depth'):
                        max_depth = max(max_depth, node.depth)

            if affected_nodes:
                paths = self._find_critical_paths(node_id, affected_nodes)
                critical_paths = paths

        except nx.NetworkXError:
            pass

        return ImpactReport(
            source_id=source_id,
            affected_nodes=affected_nodes,
            total_affected=len(affected_nodes),
            max_depth=max_depth,
            critical_paths=critical_paths,
            metadata={"analysis_type": "downstream_impact"}
        )

    def _find_critical_paths(
        self,
        source_id: str,
        target_ids: List[str]
    ) -> List[List[str]]:
        """查找关键路径"""
        paths: List[List[str]] = []

        try:
            for target_id in target_ids[:5]:
                if source_id != target_id:
                    try:
                        path = nx.shortest_path(
                            self.tracker.lineage_graph,
                            source_id,
                            target_id
                        )
                        paths.append(path)
                    except nx.NetworkXNoPath:
                        continue
        except Exception:
            pass

        return paths

    def compute_upstream_impact(self, data_id: str) -> ImpactReport:
        """上游影响分析：计算哪些上游受影响"""
        node_id = f"node_{data_id}"

        if node_id not in self.tracker._node_index:
            return ImpactReport(
                source_id=data_id,
                affected_nodes=[],
                total_affected=0,
                max_depth=0,
                critical_paths=[]
            )

        affected_nodes: List[str] = []

        if node_id in self.tracker.lineage_graph:
            try:
                ancestors = nx.ancestors(self.tracker.lineage_graph, node_id)
                affected_nodes = list(ancestors)
            except nx.NetworkXError:
                pass

        return ImpactReport(
            source_id=data_id,
            affected_nodes=affected_nodes,
            total_affected=len(affected_nodes),
            max_depth=0,
            critical_paths=[],
            metadata={"analysis_type": "upstream_impact"}
        )


import networkx as nx
