"""
F10: 概念节点安全 - 实现
"""
import hashlib
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class ScanStatus(Enum):
    CLEAN = "CLEAN"
    WARNING = "WARNING"
    BLOCKED = "BLOCKED"


class SecurityException(Exception):
    pass


class ConceptValidationError(SecurityException):
    pass


@dataclass
class IntegrityResult:
    is_integral: bool
    tampering_detected: bool
    computed_hash: str
    stored_hash: str


@dataclass
class ConceptNode:
    concept_id: str
    definition: str
    confidence: float
    source_chunk_id: str
    model_id: str
    created_at: str = ""
    definition_hash: str = ""
    status: str = "PENDING"
    review_signature: Optional[str] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = ""
        if not self.definition_hash:
            self.definition_hash = hashlib.sha256(
                self.definition.encode()
            ).hexdigest()

    @property
    def should_auto_approve(self) -> bool:
        return self.confidence >= 0.95

    @property
    def requires_manual_review(self) -> bool:
        return 0.7 <= self.confidence < 0.95


APPROVED_MODELS = [
    "claude-3-5-sonnet",
    "claude-3-opus",
    "gpt-4o",
    "gpt-4-turbo",
    "gemini-1-5-pro",
]


class KnowledgeGraphSecurity:
    def __init__(self):
        self._concepts: Dict[str, ConceptNode] = {}

    def create_concept_node(
        self,
        definition: str,
        source_chunk_id: str,
        model_id: str,
        confidence: float = 0.9,
    ) -> ConceptNode:
        if source_chunk_id is None:
            raise ConceptValidationError("source_chunk_id is required")

        if model_id not in APPROVED_MODELS:
            raise SecurityException(f"Model {model_id} not in approved list")

        if confidence < 0.7:
            node = ConceptNode(
                concept_id=f"c-{len(self._concepts) + 1}",
                definition=definition,
                confidence=confidence,
                source_chunk_id=source_chunk_id,
                model_id=model_id,
                status="REJECTED",
            )
        else:
            node = ConceptNode(
                concept_id=f"c-{len(self._concepts) + 1}",
                definition=definition,
                confidence=confidence,
                source_chunk_id=source_chunk_id,
                model_id=model_id,
            )
            self._concepts[node.concept_id] = node

        return node

    def verify_integrity(self, node: ConceptNode) -> "IntegrityResult":
        computed_hash = hashlib.sha256(node.definition.encode()).hexdigest()
        is_integral = computed_hash == node.definition_hash

        return IntegrityResult(
            is_integral=is_integral,
            tampering_detected=not is_integral,
            computed_hash=computed_hash,
            stored_hash=node.definition_hash,
        )

    def verify_and_approve(
        self, concept_id: str, reviewer_id: Optional[str]
    ) -> Dict[str, Any]:
        if reviewer_id is None:
            raise SecurityException("Reviewer ID is required")

        if concept_id not in self._concepts:
            raise ConceptValidationError(f"Concept {concept_id} not found")

        node = self._concepts[concept_id]
        node.status = "APPROVED"
        node.review_signature = f"sig-{reviewer_id}"

        return {"approved": True, "concept_id": concept_id}
