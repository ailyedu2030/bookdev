"""
TermRepository - 术语仓储

提供术语和概念相关的数据库操作。
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Concept, Term
from db.repositories.base_repository import BaseRepository


class TermRepository(BaseRepository[Term]):
    """术语仓储类"""

    def __init__(self, session: AsyncSession):
        super().__init__(Term, session)

    async def get_by_term(self, term: str) -> Term | None:
        """根据术语获取术语记录"""
        return await self.get_one(term=term)

    async def get_by_domain(
        self, domain: str, *, locked: bool | None = None
    ) -> Sequence[Term]:
        """根据领域获取术语"""
        filters = {"domain": domain}
        if locked is not None:
            filters["locked"] = locked
        return await self.find_all(filters=filters, order_by="term")

    async def get_locked_terms(self) -> Sequence[Term]:
        """获取所有已锁定的术语"""
        return await self.find_all(filters={"locked": True}, order_by="term")

    async def get_unlocked_terms(self) -> Sequence[Term]:
        """获取所有未锁定的术语"""
        return await self.find_all(filters={"locked": False}, order_by="term")

    async def search_by_term(
        self, term_query: str, *, limit: int = 20
    ) -> Sequence[Term]:
        """搜索术语"""
        stmt = (
            select(Term)
            .where(
                or_(
                    Term.term.ilike(f"%{term_query}%"),
                    Term.synonyms.any(term_query),
                )
            )
            .order_by(Term.term)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def search_by_definition(
        self, definition_query: str, *, limit: int = 20
    ) -> Sequence[Term]:
        """根据定义内容搜索术语"""
        stmt = (
            select(Term)
            .where(Term.definition.ilike(f"%{definition_query}%"))
            .order_by(Term.term)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def create_term(
        self,
        term: str,
        definition: str,
        domain: str | None = None,
        synonyms: list[str] | None = None,
        **kwargs,
    ) -> Term:
        """创建术语的便捷方法"""
        return await self.create(
            term=term,
            definition=definition,
            domain=domain,
            synonyms=synonyms or [],
            **kwargs,
        )

    async def lock_term(self, term_id: uuid.UUID) -> Term | None:
        """锁定术语"""
        return await self.update(term_id, locked=True)

    async def unlock_term(self, term_id: uuid.UUID) -> Term | None:
        """解锁术语"""
        return await self.update(term_id, locked=False)

    async def add_synonym(
        self, term_id: uuid.UUID, synonym: str
    ) -> Term | None:
        """添加同义词"""
        term = await self.get_by_id(term_id)
        if term:
            current_synonyms = list(term.synonyms) if term.synonyms else []
            if synonym not in current_synonyms:
                current_synonyms.append(synonym)
                term.synonyms = current_synonyms
                await self._session.flush()
                await self._session.refresh(term)
            return term
        return None

    async def remove_synonym(
        self, term_id: uuid.UUID, synonym: str
    ) -> Term | None:
        """移除同义词"""
        term = await self.get_by_id(term_id)
        if term:
            current_synonyms = list(term.synonyms) if term.synonyms else []
            if synonym in current_synonyms:
                current_synonyms.remove(synonym)
                term.synonyms = current_synonyms
                await self._session.flush()
                await self._session.refresh(term)
            return term
        return None

    async def find_similar_terms(
        self, term_id: uuid.UUID, threshold: float = 0.7, limit: int = 100
    ) -> Sequence[Term]:
        """查找相似术语 - 使用SQL层面操作避免N+1查询,添加limit限制"""
        term = await self.get_by_id(term_id)
        if not term or not term.synonyms:
            return []

        term_synonyms = term.synonyms
        if not term_synonyms:
            return []

        # 使用SQL的重叠数组检查 - 遍历每个同义词检查是否有重叠
        # 使用PostgreSQL的 && 数组重叠运算符
        conditions = [Term.id != term_id]

        # 构建同义词重叠条件：Term.synonyms && [syn1, syn2, ...]
        # 使用 func.array intersect 来检测
        # 同义词列表
        synonyms_list = list(term_synonyms)

        # 使用 OR 条件：有共同同义词 OR 同领域
        overlap_conditions = []
        for syn in synonyms_list:
            # 检查每个同义词是否存在于另一个术语的同义词数组中
            overlap_conditions.append(Term.synonyms.any(syn))

        if overlap_conditions:
            conditions.append(or_(*overlap_conditions, Term.domain == term.domain))
        else:
            conditions.append(Term.domain == term.domain)

        stmt = (
            select(Term)
            .where(and_(*conditions))
            .limit(limit)
        )

        result = await self._session.execute(stmt)
        return result.scalars().all()


class ConceptRepository(BaseRepository[Concept]):
    """概念仓储类"""

    def __init__(self, session: AsyncSession):
        super().__init__(Concept, session)

    async def get_by_name(self, name: str) -> Concept | None:
        """根据名称获取概念"""
        return await self.get_one(name=name)

    async def get_by_domain(
        self, domain: str, *, locked: bool | None = None
    ) -> Sequence[Concept]:
        """根据领域获取概念"""
        filters = {"domain": domain}
        if locked is not None:
            filters["locked"] = locked
        return await self.find_all(filters=filters, order_by="name")

    async def get_locked_concepts(self) -> Sequence[Concept]:
        """获取所有已锁定的概念"""
        return await self.find_all(filters={"locked": True}, order_by="name")

    async def get_unlocked_concepts(self) -> Sequence[Concept]:
        """获取所有未锁定的概念"""
        return await self.find_all(filters={"locked": False}, order_by="name")

    async def search_by_name(
        self, name_query: str, *, limit: int = 20
    ) -> Sequence[Concept]:
        """搜索概念"""
        stmt = (
            select(Concept)
            .where(
                or_(
                    Concept.name.ilike(f"%{name_query}%"),
                    Concept.related_terms.any(name_query),
                )
            )
            .order_by(Concept.name)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def search_by_definition(
        self, definition_query: str, *, limit: int = 20
    ) -> Sequence[Concept]:
        """根据定义内容搜索概念"""
        stmt = (
            select(Concept)
            .where(Concept.definition.ilike(f"%{definition_query}%"))
            .order_by(Concept.name)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def create_concept(
        self,
        name: str,
        definition: str,
        domain: str | None = None,
        related_terms: list[str] | None = None,
        **kwargs,
    ) -> Concept:
        """创建概念的便捷方法"""
        return await self.create(
            name=name,
            definition=definition,
            domain=domain,
            related_terms=related_terms or [],
            **kwargs,
        )

    async def lock_concept(self, concept_id: uuid.UUID) -> Concept | None:
        """锁定概念"""
        return await self.update(concept_id, locked=True)

    async def unlock_concept(self, concept_id: uuid.UUID) -> Concept | None:
        """解锁概念"""
        return await self.update(concept_id, locked=False)

    async def get_by_source_chapter(
        self, chapter_id: uuid.UUID
    ) -> Sequence[Concept]:
        """获取源自特定章节的概念"""
        return await self.find_all(
            filters={"source_chapter_id": chapter_id},
            order_by="name",
        )

    async def add_related_term(
        self, concept_id: uuid.UUID, term: str
    ) -> Concept | None:
        """添加关联术语"""
        concept = await self.get_by_id(concept_id)
        if concept:
            current_terms = (
                list(concept.related_terms) if concept.related_terms else []
            )
            if term not in current_terms:
                current_terms.append(term)
                concept.related_terms = current_terms
                await self._session.flush()
                await self._session.refresh(concept)
            return concept
        return None

    async def remove_related_term(
        self, concept_id: uuid.UUID, term: str
    ) -> Concept | None:
        """移除关联术语"""
        concept = await self.get_by_id(concept_id)
        if concept:
            current_terms = (
                list(concept.related_terms) if concept.related_terms else []
            )
            if term in current_terms:
                current_terms.remove(term)
                concept.related_terms = current_terms
                await self._session.flush()
                await self._session.refresh(concept)
            return concept
        return None
