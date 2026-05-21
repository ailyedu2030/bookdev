"""
F06: Tier1数值核实引擎 - 数据血缘追踪实现
"""
import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class NodeStatus(Enum):
    DRAFT = "DRAFT"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"


@dataclass
class DataNode:
    data_id: str
    value: Any
    source: str
    is_raw: bool = True
    formula: str | None = None
    input_data_ids: list[str] = field(default_factory=list)
    depth: int = 0
    status: NodeStatus = NodeStatus.DRAFT
    provenance: list[str] = field(default_factory=list)
    derived_from: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    tampered: bool = False

    def add_derived_node(self, derived_id: str):
        """记录派生出哪些数据"""
        if derived_id not in self.derived_from:
            self.derived_from.append(derived_id)


@dataclass
class LineageResult:
    success: bool
    node: DataNode | None = None
    rejected: bool = False
    reason: str = ""


class DataLineageTracker:
    """数据血缘追踪器"""

    DEFAULT_MAX_DEPTH = 3
    DEFAULT_MAX_DERIVATION_CHAIN = 5

    def __init__(self, max_depth: int = DEFAULT_MAX_DEPTH, max_derivation_chain: int = DEFAULT_MAX_DERIVATION_CHAIN):
        self.max_depth = max_depth
        self.max_derivation_chain = max_derivation_chain
        self._nodes: dict[str, DataNode] = {}
        self._lock = asyncio.Lock()

        self.VALUE_RANGES = {
            "population": {"min": 0, "max": 15000000000},
            "gdp": {"min": 0, "max": 300000000000000},
            "price": {"min": 0, "max": 1000000000000},
        }

    async def register_raw_data(self, data_id: str, value: Any, source: str) -> LineageResult:
        """注册原始数据"""
        async with self._lock:
            range_result = self._check_value_range(value)
            if range_result:
                return LineageResult(success=False, rejected=True, reason=f"INVALID_RANGE: {range_result}")

            node = DataNode(
                data_id=data_id, value=value, source=source, is_raw=True, depth=0, status=NodeStatus.VERIFIED
            )
            node.provenance = [source]
            self._nodes[data_id] = node
            return LineageResult(success=True, node=node)

    async def register_derived_data(
        self, data_id: str, formula: str | None, input_data_ids: list[str], **kwargs
    ) -> LineageResult:
        """注册派生数据"""
        async with self._lock:
            if formula is None:
                return LineageResult(
                    success=False, rejected=True, reason="MISSING_FORMULA: Derived data must include formula"
                )

            for input_id in input_data_ids:
                if input_id not in self._nodes:
                    return LineageResult(
                        success=False, rejected=True, reason=f"UNKNOWN_INPUT: Input data {input_id} not found"
                    )

            max_input_depth = max(self._nodes[inp_id].depth for inp_id in input_data_ids)
            new_depth = max_input_depth + 1

            if new_depth > self.max_depth:
                return LineageResult(
                    success=False,
                    rejected=True,
                    reason=f"DEPTH_EXCEEDED: Max depth is {self.max_depth}, got depth {new_depth}",
                )

            derivation_chain_length = self._calculate_derivation_chain(input_data_ids)
            if derivation_chain_length > self.max_derivation_chain:
                return LineageResult(
                    success=False,
                    rejected=True,
                    reason=f"DERIVATION_CHAIN_EXCEEDED: Max chain is {self.max_derivation_chain}",
                )

            derived_value = kwargs.get("value")
            node = DataNode(
                data_id=data_id,
                value=derived_value,
                source="derived",
                is_raw=False,
                formula=formula,
                input_data_ids=input_data_ids,
                depth=new_depth,
                status=NodeStatus.VERIFIED,
            )

            provenance = []
            for inp_id in input_data_ids:
                provenance.extend(self._nodes[inp_id].provenance)
                self._nodes[inp_id].add_derived_node(data_id)

            node.provenance = list(set(provenance))
            self._nodes[data_id] = node

            return LineageResult(success=True, node=node)

    def get_node(self, data_id: str) -> DataNode | None:
        """获取数据节点"""
        return self._nodes.get(data_id)

    def get_propagation_chain(self, data_id: str) -> list[DataNode]:
        """获取传播链 - 原始数据在前，派生数据在后"""
        if data_id not in self._nodes:
            raise ValueError(f"Data node {data_id} not found")

        chain = []
        visited = set()
        self._build_propagation_chain(data_id, chain, visited)
        # Reverse to ensure raw data comes first
        chain.reverse()
        return chain

    def _build_propagation_chain(self, data_id: str, chain: list[DataNode], visited: set[str]):
        """递归构建传播链 - 深度优先，后序遍历确保原始数据在前"""
        if data_id in visited:
            return

        node = self._nodes.get(data_id)
        if node is None:
            return

        visited.add(data_id)

        # First process all inputs (children)
        if not node.is_raw:
            for input_id in node.input_data_ids:
                self._build_propagation_chain(input_id, chain, visited)

        # Then add current node (post-order ensures raw data comes first after reverse)
        chain.append(node)

    def get_all_nodes(self) -> list[DataNode]:
        """获取所有节点"""
        return list(self._nodes.values())

    def detect_anomaly(self, data_id: str) -> bool:
        """检测异常"""
        node = self._nodes.get(data_id)
        if node is None:
            return True

        range_result = self._check_value_range(node.value)
        if range_result:
            return True

        return False

    def _check_value_range(self, value: Any) -> str | None:
        """检查值是否在合理范围内"""
        if not isinstance(value, int | float):
            return None

        for range_info in self.VALUE_RANGES.values():
            if range_info["min"] <= value <= range_info["max"]:
                return None

        return "INVALID_RANGE"

    def _calculate_derivation_chain(self, input_data_ids: list[str]) -> int:
        """计算派生链长度 - 从root到当前节点的链长度

        派生链长度是指从根节点到当前节点的步数。
        如果当前节点的输入是原始数据(depth=0)，则链长度为1。
        如果输入是派生数据(depth=1)，则链长度为2，以此类推。
        """
        max_chain_length = 0
        for inp_id in input_data_ids:
            inp_node = self._nodes.get(inp_id)
            if inp_node:
                # 链长度 = 输入节点的深度 + 1
                # depth=0 表示原始数据，链长度为1
                # depth=1 表示由原始数据派生，链长度为2
                chain_length = inp_node.depth + 1
                max_chain_length = max(max_chain_length, chain_length)
        return max_chain_length

    def get_root_nodes(self) -> list[DataNode]:
        """获取所有根节点（原始数据）"""
        return [node for node in self._nodes.values() if node.is_raw]

    def get_derivation_depth(self, data_id: str) -> int:
        """获取节点的派生深度（从根节点开始的步数）"""
        node = self._nodes.get(data_id)
        if not node:
            return 0

        if node.is_raw:
            return 0

        # 沿着输入链递归计算最大深度
        max_depth = 0
        for input_id in node.input_data_ids:
            input_depth = self.get_derivation_depth(input_id)
            max_depth = max(max_depth, input_depth)

        return max_depth + 1
