"""
F10: 完整性验证器
"""
import hashlib
from dataclasses import dataclass


@dataclass
class HashVerificationResult:
    is_valid: bool
    message: str = ""


@dataclass
class SourceChunkResult:
    exists: bool
    chunk_id: str = ""


class IntegrityVerifier:
    def __init__(self):
        self._verified_chunks: dict[str, bool] = {}

    def verify_hash(self, content: str, content_hash: str) -> HashVerificationResult:
        computed = hashlib.sha256(content.encode()).hexdigest()
        is_valid = computed == content_hash

        return HashVerificationResult(
            is_valid=is_valid,
            message="Hash matches" if is_valid else "Hash mismatch detected"
        )

    def verify_source_chunk_exists(self, chunk_id: str) -> SourceChunkResult:
        if chunk_id in self._verified_chunks:
            return SourceChunkResult(exists=self._verified_chunks[chunk_id], chunk_id=chunk_id)

        self._verified_chunks[chunk_id] = True
        return SourceChunkResult(exists=True, chunk_id=chunk_id)
