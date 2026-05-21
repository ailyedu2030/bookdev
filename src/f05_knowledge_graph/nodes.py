"""
F05: 知识图谱节点定义
"""

import hashlib
from dataclasses import dataclass, field
from enum import Enum


class NodeStatus(Enum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    PUBLISHED = "published"


class NodeType(Enum):
    CHAPTER = "Chapter"
    SECTION = "Section"
    SUBSECTION = "Subsection"
    CONCEPT = "Concept"
    TERM = "Term"


@dataclass
class BaseNode:
    """节点基类"""
    id: str
    title: str
    order: int = 0
    status: NodeStatus = NodeStatus.DRAFT
    type: str = ""

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type or "",
            "title": self.title,
            "order": self.order,
            "status": self.status.value if isinstance(self.status, NodeStatus) else self.status,
        }


@dataclass
class ChapterNode(BaseNode):
    """章节点"""
    id: str
    title: str
    order: int
    status: NodeStatus = NodeStatus.DRAFT
    word_count: int = 0
    version: str = "1.0"

    def __post_init__(self):
        self.type = "Chapter"

    def to_dict(self):
        d = super().to_dict()
        d.update({
            "word_count": self.word_count,
            "version": self.version,
        })
        return d


@dataclass
class SectionNode(BaseNode):
    """节节点"""
    id: str
    title: str
    order: int
    status: NodeStatus = NodeStatus.DRAFT
    word_count: int = 0
    parent_chapter_id: str = ""

    def __post_init__(self):
        self.type = "Section"

    def to_dict(self):
        d = super().to_dict()
        d.update({
            "parent_chapter_id": self.parent_chapter_id,
            "word_count": self.word_count,
        })
        return d


@dataclass
class SubsectionNode(BaseNode):
    """小节节点"""
    id: str
    title: str
    order: int
    status: NodeStatus = NodeStatus.DRAFT
    content: str = ""
    parent_section_id: str = ""

    def __post_init__(self):
        self.type = "Subsection"

    def to_dict(self):
        d = super().to_dict()
        d.update({
            "parent_section_id": self.parent_section_id,
            "content": self.content,
        })
        return d


@dataclass
class ConceptNode:
    """概念节点"""
    id: str
    name: str
    definition: str
    domain: str
    related_terms: list[str] = field(default_factory=list)
    source_chapter_id: str | None = None
    definition_hash: str | None = None

    def __post_init__(self):
        self.type = "Concept"
        if self.definition_hash is None:
            self.definition_hash = hashlib.sha256(self.definition.encode()).hexdigest()

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "definition": self.definition,
            "domain": self.domain,
            "related_terms": self.related_terms,
            "source_chapter_id": self.source_chapter_id,
            "definition_hash": self.definition_hash,
        }


@dataclass
class TermNode:
    """术语节点"""
    id: str
    term: str
    definition: str
    domain: str
    synonyms: list[str] = field(default_factory=list)
    first_defined_at: str | None = None

    def __post_init__(self):
        self.type = "Term"

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "term": self.term,
            "definition": self.definition,
            "synonyms": self.synonyms,
            "domain": self.domain,
            "first_defined_at": self.first_defined_at,
        }


def create_node(node_type: str, **kwargs):
    """节点工厂函数"""
    node_classes = {
        "Chapter": ChapterNode,
        "Section": SectionNode,
        "Subsection": SubsectionNode,
        "Concept": ConceptNode,
        "Term": TermNode,
    }
    node_class = node_classes.get(node_type)
    if node_class is None:
        raise ValueError(f"Unknown node type: {node_type}")
    return node_class(**kwargs)
