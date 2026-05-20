"""
F26: 血缘追踪系统 - 节点数据结构
定义血缘节点、边和数据源类型
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4


class NodeType(Enum):
    """节点类型枚举"""
    SOURCE = "source"
    TRANSFORM = "transform"
    AGGREGATE = "aggregate"
    FILTER = "filter"
    JOIN = "join"
    OUTPUT = "output"


@dataclass
class DataSource:
    """数据源定义"""
    source_id: str
    source_type: str
    name: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self):
        return hash(self.source_id)

    def __eq__(self, other):
        if not isinstance(other, DataSource):
            return False
        return self.source_id == other.source_id


@dataclass
class LineageNode:
    """血缘节点"""
    node_id: str
    data_id: str
    node_type: NodeType
    source: DataSource
    transformation: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    parents: List[str] = field(default_factory=list)
    children: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    depth: int = 0

    def __hash__(self):
        return hash(self.node_id)

    def __eq__(self, other):
        if not isinstance(other, LineageNode):
            return False
        return self.node_id == other.node_id


@dataclass
class LineageEdge:
    """血缘边"""
    edge_id: str
    source_node_id: str
    target_node_id: str
    edge_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self):
        return hash(self.edge_id)


@dataclass
class ImpactReport:
    """影响分析报告"""
    source_id: str
    affected_nodes: List[str]
    total_affected: int
    max_depth: int
    critical_paths: List[List[str]]
    metadata: Dict[str, Any] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
