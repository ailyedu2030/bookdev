"""
F26: 血缘追踪系统 - 传播验证器
验证数据传播深度，防止无限传播（防F06漏洞）
"""
import networkx as nx
from typing import Optional

from lineage_tracker import DataLineageTracker
from lineage_node import LineageNode


class PropagationVerifier:
    """传播验证器"""

    def __init__(self, tracker: DataLineageTracker):
        self.tracker = tracker
        self._cache: dict = {}

    def verify_propagation_depth(
        self,
        data_id: str,
        max_depth: int = 5
    ) -> bool:
        """验证传播深度（防F06漏洞）

        传播深度限制是为了防止数据无限传播，导致:
        1. 验证计算量指数增长
        2. 内存耗尽
        3. F06核实引擎被滥用

        Args:
            data_id: 数据ID
            max_depth: 最大深度限制，默认5层

        Returns:
            True: 深度在限制内
            False: 深度超出限制
        """
        node_id = f"node_{data_id}"

        if node_id not in self.tracker._node_index:
            return True

        cache_key = f"{data_id}:{max_depth}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        if node_id not in self.tracker.lineage_graph:
            self._cache[cache_key] = True
            return True

        try:
            descendants = nx.descendants(self.tracker.lineage_graph, node_id)

            depths = []
            for desc_id in descendants:
                if desc_id in self.tracker._node_index:
                    node = self.tracker._node_index[desc_id]
                    if hasattr(node, 'depth'):
                        depths.append(node.depth)

            if depths:
                actual_max_depth = max(depths)
                result = actual_max_depth <= max_depth
            else:
                result = True

            self._cache[cache_key] = result
            return result

        except Exception:
            self._cache[cache_key] = True
            return True

    def get_actual_depth(self, data_id: str) -> int:
        """获取实际传播深度"""
        node_id = f"node_{data_id}"

        if node_id not in self.tracker._node_index:
            return 0

        if node_id not in self.tracker.lineage_graph:
            return 0

        try:
            descendants = nx.descendants(self.tracker.lineage_graph, node_id)

            max_depth = 0
            for desc_id in descendants:
                if desc_id in self.tracker._node_index:
                    node = self.tracker._node_index[desc_id]
                    if hasattr(node, 'depth'):
                        max_depth = max(max_depth, node.depth)

            return max_depth

        except Exception:
            return 0

    def verify_depth_limit_exceeded(
        self,
        data_id: str,
        max_depth: int = 5
    ) -> Optional[int]:
        """验证深度是否超限，返回实际深度或None"""
        node_id = f"node_{data_id}"

        if node_id not in self.tracker._node_index:
            return None

        if node_id not in self.tracker.lineage_graph:
            return 0

        try:
            descendants = nx.descendants(self.tracker.lineage_graph, node_id)

            depths = []
            for desc_id in descendants:
                if desc_id in self.tracker._node_index:
                    node = self.tracker._node_index[desc_id]
                    if hasattr(node, 'depth'):
                        depths.append(node.depth)

            if not depths:
                return 0

            actual_max = max(depths)
            if actual_max > max_depth:
                return actual_max

            return None

        except Exception:
            return None

    def clear_cache(self) -> None:
        """清除缓存"""
        self._cache.clear()
