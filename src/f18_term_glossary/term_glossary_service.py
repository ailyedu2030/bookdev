"""
F18: 术语表服务

提供术语的注册、管理、查询功能
"""

import uuid
from dataclasses import dataclass, field


@dataclass
class RegisteredTerm:
    """注册术语"""

    id: str
    term: str
    definition: str
    domain: str
    synonyms: list[str] = field(default_factory=list)
    locked: bool = False
    version: int = 1
    first_defined_at: str | None = None
    usage_locations: list[str] = field(default_factory=list)


@dataclass
class OperationResult:
    """操作结果"""

    success: bool
    term: RegisteredTerm | None = None
    error: str | None = None


class TermGlossaryService:
    """术语表服务"""

    def __init__(self):
        self._terms: dict[str, RegisteredTerm] = {}
        self._terms_by_name: dict[str, str] = {}  # name -> id
        self._synonym_index: dict[str, str] = {}  # synonym -> term_id

    def register_term(
        self,
        term: str,
        definition: str,
        domain: str,
        synonyms: list[str] = None,
        locked: bool = False,
    ) -> OperationResult:
        """注册新术语"""
        if term in self._terms_by_name:
            return OperationResult(success=False, error=f"Term '{term}' already exists")

        term_id = str(uuid.uuid4())
        registered_term = RegisteredTerm(
            id=term_id,
            term=term,
            definition=definition,
            domain=domain,
            synonyms=synonyms or [],
            locked=locked,
        )

        self._terms[term_id] = registered_term
        self._terms_by_name[term] = term_id

        for syn in synonyms or []:
            self._synonym_index[syn.lower()] = term_id

        return OperationResult(success=True, term=registered_term)

    def get_term(self, term_id: str) -> RegisteredTerm | None:
        """通过ID获取术语"""
        return self._terms.get(term_id)

    def find_term(self, term_or_synonym: str) -> RegisteredTerm | None:
        """通过名称或同义词查找术语"""
        term_id = self._terms_by_name.get(term_or_synonym)
        if term_id:
            return self._terms.get(term_id)

        term_id = self._synonym_index.get(term_or_synonym.lower())
        if term_id:
            return self._terms.get(term_id)

        return None

    def get_terms_by_domain(self, domain: str) -> list[RegisteredTerm]:
        """按领域获取术语"""
        return [term for term in self._terms.values() if term.domain == domain]

    def add_synonym(self, term_id: str, synonym: str) -> OperationResult:
        """为术语添加同义词"""
        term = self._terms.get(term_id)
        if not term:
            return OperationResult(success=False, error="Term not found")

        if synonym not in term.synonyms:
            term.synonyms.append(synonym)
            self._synonym_index[synonym.lower()] = term_id

        return OperationResult(success=True, term=term)

    def update_term_definition(self, term_id: str, new_definition: str) -> OperationResult:
        """更新术语定义"""
        term = self._terms.get(term_id)
        if not term:
            return OperationResult(success=False, error="Term not found")

        if term.locked:
            return OperationResult(success=False, error="Term is locked. Unlock before updating.")

        term.definition = new_definition
        term.version += 1

        return OperationResult(success=True, term=term)

    def unlock_term(self, term_id: str) -> OperationResult:
        """解锁术语"""
        term = self._terms.get(term_id)
        if not term:
            return OperationResult(success=False, error="Term not found")

        term.locked = False
        return OperationResult(success=True, term=term)

    def lock_term(self, term_id: str) -> OperationResult:
        """锁定术语"""
        term = self._terms.get(term_id)
        if not term:
            return OperationResult(success=False, error="Term not found")

        term.locked = True
        return OperationResult(success=True, term=term)

    def track_usage(self, term_id: str, location: str) -> None:
        """追踪术语使用位置"""
        term = self._terms.get(term_id)
        if term and location not in term.usage_locations:
            term.usage_locations.append(location)

    def get_term_usage(self, term_id: str) -> list[str]:
        """获取术语使用位置"""
        term = self._terms.get(term_id)
        return term.usage_locations if term else []

    def get_all_terms(self) -> list[RegisteredTerm]:
        """获取所有术语"""
        return list(self._terms.values())

    def export(self) -> dict:
        """导出术语表"""
        return {
            "terms": [
                {
                    "id": t.id,
                    "term": t.term,
                    "definition": t.definition,
                    "domain": t.domain,
                    "synonyms": t.synonyms,
                    "locked": t.locked,
                    "version": t.version,
                    "usage_locations": t.usage_locations,
                }
                for t in self._terms.values()
            ]
        }

    def import_(self, data: dict) -> None:
        """导入术语表"""
        self._terms.clear()
        self._terms_by_name.clear()
        self._synonym_index.clear()

        for term_data in data.get("terms", []):
            term = RegisteredTerm(
                id=term_data["id"],
                term=term_data["term"],
                definition=term_data["definition"],
                domain=term_data["domain"],
                synonyms=term_data.get("synonyms", []),
                locked=term_data.get("locked", False),
                version=term_data.get("version", 1),
                usage_locations=term_data.get("usage_locations", []),
            )
            self._terms[term.id] = term
            self._terms_by_name[term.term] = term.id
            for syn in term.synonyms:
                self._synonym_index[syn.lower()] = term.id
