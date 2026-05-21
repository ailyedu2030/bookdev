"""
F07: DOI强制解析服务 - DOI验证器
"""
import asyncio
import hashlib
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from f07_doi_verification.crossref_client import CrossRefClient


class DOIValidationStatus(Enum):
    VALID = "VALID"
    INVALID_FORMAT = "INVALID_FORMAT"
    NOT_FOUND = "NOT_FOUND"
    EXISTS = "EXISTS"


@dataclass
class DOIResult:
    exists: bool
    doi: str
    reason: str = ""
    metadata: dict[str, Any] | None = None
    status: DOIValidationStatus = DOIValidationStatus.VALID


@dataclass
class Citation:
    doi: str
    fact_hash: str
    position: dict[str, Any] | None = None


class CitationValidationError(Exception):
    """引用格式验证错误"""

    pass


@dataclass
class CitationVerificationResult:
    is_valid: bool
    doi: str
    fact_hash: str
    mismatch_reason: str | None = None


@dataclass
class Fact:
    fact_hash: str
    content: str
    source_refs: list[str]
    versions: list[dict[str, Any]] = field(default_factory=list)
    is_verified: bool = False
    verifier_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class FactRegistry:
    """全局事实注册表"""

    def __init__(self):
        self._facts: dict[str, Fact] = {}

    def register_fact(self, content: str, source_refs: list[str]) -> str:
        """注册新事实，返回fact_hash"""
        fact_hash = hashlib.sha256(content.encode()).hexdigest()

        fact = Fact(fact_hash=fact_hash, content=content, source_refs=source_refs, versions=[], is_verified=False)

        self._facts[fact_hash] = fact
        return fact_hash

    def verify_fact(self, fact_hash: str, verifier_id: str) -> bool:
        """核实事实"""
        if fact_hash not in self._facts:
            return False

        fact = self._facts[fact_hash]
        fact.is_verified = True
        fact.verifier_id = verifier_id
        return True

    def add_version(self, fact_hash: str, new_content: str, reason: str) -> str:
        """添加新版本，返回新版本hash"""
        if fact_hash not in self._facts:
            raise ValueError(f"Fact {fact_hash} not found")

        old_fact = self._facts[fact_hash]
        new_hash = hashlib.sha256(new_content.encode()).hexdigest()

        old_fact.versions.append({"content": new_content, "reason": reason, "timestamp": datetime.now(UTC).isoformat()})

        new_fact = Fact(
            fact_hash=new_hash,
            content=new_content,
            source_refs=old_fact.source_refs.copy(),
            versions=old_fact.versions.copy(),
            is_verified=False,
        )

        self._facts[new_hash] = new_fact
        return new_hash

    def get_fact_history(self, fact_hash: str) -> list[dict[str, Any]]:
        """获取事实的完整版本历史"""
        if fact_hash not in self._facts:
            return []

        fact = self._facts[fact_hash]
        history = [{"content": fact.content, "version": 0}]

        for i, version in enumerate(fact.versions):
            history.append({"content": version["content"], "reason": version["reason"], "version": i + 1})

        return history

    def get_fact(self, fact_hash: str) -> Fact | None:
        """获取事实"""
        return self._facts.get(fact_hash)


class DOIVerifier:
    """DOI验证器"""

    DOI_PREFIX_PATTERN = re.compile(r"^10\.\d{4,}/[^\s]+$")

    def __init__(
        self,
        timeout_seconds: float = 5.0,
        fact_registry: FactRegistry | None = None,
        crossref_client: CrossRefClient | None = None,
    ):
        self.timeout_seconds = timeout_seconds
        self._fact_registry = fact_registry or FactRegistry()
        # Reuse the provided CrossRefClient or create one
        self._crossref_client = crossref_client or CrossRefClient(timeout=timeout_seconds)

    async def verify(self, doi: str) -> DOIResult:
        """验证DOI是否存在"""
        if not self._is_valid_doi_format(doi):
            return DOIResult(
                exists=False,
                doi=doi,
                reason="INVALID_FORMAT: DOI must match pattern 10.XXXX/...",
                status=DOIValidationStatus.INVALID_FORMAT,
            )

        try:
            metadata = await self._fetch_doi_metadata(doi)

            if metadata is None:
                return DOIResult(
                    exists=False, doi=doi, reason="DOI not found in CrossRef", status=DOIValidationStatus.NOT_FOUND
                )

            return DOIResult(exists=True, doi=doi, metadata=metadata, status=DOIValidationStatus.EXISTS)

        except TimeoutError:
            return DOIResult(
                exists=False,
                doi=doi,
                reason="TIMEOUT: DOI verification timed out",
                status=DOIValidationStatus.NOT_FOUND,
            )
        except (ValueError, TypeError, KeyError) as e:
            # Only catch expected exceptions, not system-exiting ones like KeyboardInterrupt, SystemExit
            return DOIResult(exists=False, doi=doi, reason=f"ERROR: {str(e)}", status=DOIValidationStatus.NOT_FOUND)

    def _is_valid_doi_format(self, doi: str) -> bool:
        """验证DOI格式"""
        if not doi:
            return False
        return bool(self.DOI_PREFIX_PATTERN.match(doi))

    async def _fetch_doi_metadata(self, doi: str) -> dict[str, Any] | None:
        """从CrossRef获取DOI元数据"""
        metadata = await asyncio.wait_for(self._crossref_client.fetch_doi_metadata(doi), timeout=self.timeout_seconds)
        return metadata

    def validate_citation_format(self, citation: Citation) -> None:
        """验证引用格式 - 必须包含fact_hash"""
        if not citation.fact_hash:
            raise CitationValidationError("Citation must include fact_hash for integrity verification")

        if not citation.doi:
            raise CitationValidationError("Citation must include DOI")

        if not self._is_valid_doi_format(citation.doi):
            raise CitationValidationError(f"Invalid DOI format: {citation.doi}")

    async def verify_citation_content(self, doi: str, fact_hash: str, cited_content: str) -> CitationVerificationResult:
        """验证引用内容与注册表一致"""
        expected_hash = hashlib.sha256(cited_content.encode()).hexdigest()

        if expected_hash != fact_hash:
            return CitationVerificationResult(
                is_valid=False, doi=doi, fact_hash=fact_hash, mismatch_reason="Content hash does not match fact_hash"
            )

        return CitationVerificationResult(is_valid=True, doi=doi, fact_hash=fact_hash)

    def detect_circular_reference(self, citations: list[Citation]) -> bool:
        """检测循环引用 - A引用B，B引用A即为循环
        自引用（A引用A）不算循环

        使用迭代（显式栈）实现以避免递归栈溢出
        """
        doi_to_refs: dict[str, set] = {}

        for citation in citations:
            if citation.doi not in doi_to_refs:
                doi_to_refs[citation.doi] = set()

            fact = self._fact_registry.get_fact(citation.fact_hash)
            if fact:
                doi_to_refs[citation.doi].update(fact.source_refs)

        # 使用显式栈进行迭代检测
        for start_doi in doi_to_refs:
            # 使用栈来模拟递归，栈元素为(当前节点, 路径集合)
            stack = [(start_doi, set())]

            while stack:
                current_doi, path = stack.pop()

                if current_doi in path:
                    # 发现循环
                    return True

                if current_doi in doi_to_refs:
                    new_path = path | {current_doi}
                    for ref in doi_to_refs[current_doi]:
                        if ref == current_doi:
                            continue  # 自引用不算循环
                        stack.append((ref, new_path))

        return False

    @property
    def fact_registry(self) -> FactRegistry:
        """获取事实注册表"""
        return self._fact_registry
