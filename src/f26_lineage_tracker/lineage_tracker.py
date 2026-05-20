"""
F26: 血缘追踪系统 - 主追踪器
追踪数据从来源到最终输出的完整传播路径
"""
import networkx as nx
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timezone

try:
    from .lineage_node import LineageNode, DataSource, NodeType, ImpactReport
except ImportError:
    from lineage_node import LineageNode, DataSource, NodeType, ImpactReport


class DataLineageTracker:
    """数据血缘追踪系统"""

    def __init__(self):
        self.lineage_graph = nx.DiGraph()
        self.verification_cache: Dict[str, bool] = {}
        self._node_index: Dict[str, LineageNode] = {}
        self._last_created_node_id: Optional[str] = None

    def track_provenance(
        self,
        data_id: str,
        source: DataSource,
        transformation: str,
        metadata: Dict[str, Any]
    ) -> None:
        """记录数据血缘"""
        node_id = f"node_{data_id}"

        existing_node = self._node_index.get(node_id)
        if existing_node:
            existing_node.transformation = transformation
            existing_node.metadata = metadata
            return

        source_node_id = f"node_{source.source_id}"
        parent_node_id: Optional[str] = None
        depth = 0

        if source_node_id in self._node_index:
            parent_node_id = source_node_id
            parent_node = self._node_index[parent_node_id]
            depth = getattr(parent_node, 'depth', 0) + 1
        elif self._last_created_node_id is not None:
            last_node = self._node_index.get(self._last_created_node_id)
            if last_node and last_node.source.source_id == source.source_id:
                parent_node_id = self._last_created_node_id
                depth = getattr(last_node, 'depth', 0) + 1

        node_type = self._infer_node_type(transformation)

        node = LineageNode(
            node_id=node_id,
            data_id=data_id,
            node_type=node_type,
            source=source,
            transformation=transformation,
            metadata=metadata,
            depth=depth
        )

        self._node_index[node_id] = node
        self.lineage_graph.add_node(node_id, node=node)

        if parent_node_id:
            self.lineage_graph.add_edge(parent_node_id, node_id)
            node.parents.append(parent_node_id)

            parent_node = self._node_index[parent_node_id]
            parent_node.children.append(node_id)

        self._last_created_node_id = node_id

    def _infer_node_type(self, transformation: str) -> NodeType:
        """根据转换类型推断节点类型"""
        trans_upper = transformation.upper()
        if "FILTER" in trans_upper:
            return NodeType.FILTER
        elif "AGGREGATE" in trans_upper or "GROUP" in trans_upper:
            return NodeType.AGGREGATE
        elif "JOIN" in trans_upper or "MERGE" in trans_upper:
            return NodeType.JOIN
        elif "INGEST" in trans_upper or "SOURCE" in trans_upper:
            return NodeType.SOURCE
        elif "OUTPUT" in trans_upper or "EXPORT" in trans_upper:
            return NodeType.OUTPUT
        else:
            return NodeType.TRANSFORM

    def has_lineage(self, data_id: str) -> bool:
        """检查是否存在血缘记录"""
        node_id = f"node_{data_id}"
        return node_id in self._node_index

    def get_node(self, data_id: str) -> Optional[LineageNode]:
        """获取节点"""
        node_id = f"node_{data_id}"
        return self._node_index.get(node_id)

    def get_node_count(self) -> int:
        """获取节点数量"""
        return len(self._node_index)

    def get_lineage_chain(self, data_id: str) -> List[LineageNode]:
        """获取数据血缘链"""
        node_id = f"node_{data_id}"

        if node_id not in self._node_index:
            return []

        if node_id not in self.lineage_graph:
            return [self._node_index[node_id]]

        try:
            ancestors = nx.ancestors(self.lineage_graph, node_id)
            chain_nodes = [self._node_index[n] for n in ancestors if n in self._node_index]
            chain_nodes.append(self._node_index[node_id])
            chain_nodes.sort(key=lambda n: n.depth if hasattr(n, 'depth') else 0)
            return chain_nodes
        except nx.NetworkXError:
            return [self._node_index[node_id]]

    def detect_circular_lineage(self) -> bool:
        """检测循环血缘"""
        try:
            cycle = nx.find_cycle(self.lineage_graph, orientation="original")
            return len(cycle) > 0
        except nx.NetworkXError:
            return False
        except Exception:
            return False

    def get_all_nodes(self) -> List[LineageNode]:
        """获取所有节点"""
        return list(self._node_index.values())

    def get_children(self, data_id: str) -> List[LineageNode]:
        """获取子节点"""
        node_id = f"node_{data_id}"
        if node_id not in self._node_index:
            return []

        node = self._node_index[node_id]
        return [self._node_index[child_id] for child_id in node.children if child_id in self._node_index]

    def get_parents(self, data_id: str) -> List[LineageNode]:
        """获取父节点"""
        node_id = f"node_{data_id}"
        if node_id not in self._node_index:
            return []

        node = self._node_index[node_id]
        return [self._node_index[parent_id] for parent_id in node.parents if parent_id in self._node_index]
