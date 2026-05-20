"""
F05: 知识图谱边定义
"""

from dataclasses import dataclass, field
from typing import Any, Optional
from enum import Enum


class EdgeType(Enum):
    CONTAINS = "CONTAINS"
    FOLLOWS = "FOLLOWS"
    DEFINES = "DEFINES"
    USES = "USES"
    REFERENCES = "REFERENCES"
    ASSIGNED_TO = "ASSIGNED_TO"
    REVIEWED_BY = "REVIEWED_BY"
    SIMILAR_TO = "SIMILAR_TO"


class LogicalType(Enum):
    PREREQUISITE = "prerequisite"
    SEQUENTIAL = "sequential"
    OPTIONAL = "optional"


class ReferenceType(Enum):
    DEFINITION = "definition"
    APPLICATION = "application"
    EXAMPLE = "example"
    COMPARISON = "comparison"


@dataclass
class Edge:
    """边基类"""
    edge_type: str
    source: str
    target: str
    properties: dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return {
            "edge_type": self.edge_type,
            "source": self.source,
            "target": self.target,
            "properties": self.properties,
        }


def create_edge(edge_type: str, source: str, target: str, **properties) -> Edge:
    """边工厂函数"""
    return Edge(
        edge_type=edge_type,
        source=source,
        target=target,
        properties=properties
    )
