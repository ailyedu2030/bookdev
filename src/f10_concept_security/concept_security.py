"""
F10: 概念节点安全 - 实现
"""
import hashlib
import hmac
import os
from dataclasses import dataclass
from enum import Enum
from typing import Any


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
    review_signature: str | None = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = ""
        if not self.definition_hash:
            self.definition_hash = hashlib.sha256(self.definition.encode()).hexdigest()

    @property
    def should_auto_approve(self) -> bool:
        return self.confidence >= 0.95

    @property
    def requires_manual_review(self) -> bool:
        return 0.7 <= self.confidence < 0.95


# F10-002 FIX: 从环境变量加载已批准模型列表，不再硬编码
def _load_approved_models() -> list[str]:
    """从环境变量加载已批准模型列表"""
    env_value = os.environ.get("APPROVED_MODELS")
    if env_value:
        return [m.strip() for m in env_value.split(",") if m.strip()]
    # 默认值（仅用于测试，生产应设置环境变量）
    return [
        "claude-3-5-sonnet",
        "claude-3-opus",
        "gpt-4o",
        "gpt-4-turbo",
        "gemini-1-5-pro",
    ]


APPROVED_MODELS = _load_approved_models()


# F10-001 FIX: 使用HMAC签名，需要密钥
def _get_signature_key() -> bytes:
    """获取签名的密钥"""
    key = os.environ.get("CONCEPT_SIGNATURE_KEY")
    if not key:
        raise SecurityException("MISSING_SIGNATURE_KEY", "CONCEPT_SIGNATURE_KEY environment variable not set")
    return key.encode()


class KnowledgeGraphSecurity:
    def __init__(self):
        self._concepts: dict[str, ConceptNode] = {}

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

    def _generate_approval_signature(self, concept_id: str, reviewer_id: str) -> str:
        """生成安全的HMAC签名"""
        key = _get_signature_key()
        message = f"{concept_id}:{reviewer_id}"
        signature = hmac.new(key, message.encode(), hashlib.sha256).hexdigest()
        return f"sig-{concept_id}-{reviewer_id}-{signature[:16]}"

    def verify_approval_signature(self, concept_id: str, reviewer_id: str, signature: str) -> bool:
        """验证审批签名"""
        if not signature or not signature.startswith("sig-"):
            return False

        expected = self._generate_approval_signature(concept_id, reviewer_id)
        return hmac.compare_digest(signature, expected)

    def verify_and_approve(self, concept_id: str, reviewer_id: str | None) -> dict[str, Any]:
        if reviewer_id is None:
            raise SecurityException("Reviewer ID is required")

        if concept_id not in self._concepts:
            raise ConceptValidationError(f"Concept {concept_id} not found")

        node = self._concepts[concept_id]
        node.status = "APPROVED"

        # F10-001 FIX: 使用HMAC生成安全签名，而不是简单的 f"sig-{reviewer_id}"
        node.review_signature = self._generate_approval_signature(concept_id, reviewer_id)

        return {"approved": True, "concept_id": concept_id}
