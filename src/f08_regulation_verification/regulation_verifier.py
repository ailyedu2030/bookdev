"""
F08: 法规引用核实系统 - 法规验证器
"""
import asyncio
import re
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum

from f08_regulation_verification.whitelist_manager import WhitelistManager


class VerificationTier(Enum):
    TIER1_LAW_EXISTS = "TIER1_LAW_EXISTS"
    TIER2_ARTICLE_EXISTS = "TIER2_ARTICLE_EXISTS"
    TIER3_CONTENT_RELEVANCE = "TIER3_CONTENT_RELEVANCE"


@dataclass
class RegulationResult:
    is_valid: bool
    law_name: str
    article_num: int
    reason: str = ""
    law_exists: bool = False
    article_exists: bool = False
    tier1_passed: bool = False
    tier2_passed: bool = False
    tier3_score: float = 0.0


@dataclass
class ContentRelevanceResult:
    is_valid: bool
    score: float
    reason: str = ""


class RegulationVerifier:
    """法规核实引擎 - 三级核实"""

    VAGUE_REFERENCE_PHRASES = [
        "根据相关规定",
        "按照有关法律法规",
        "依据有关政策",
        "根据有关规定",
        "按照相关规定"
    ]

    def __init__(self, whitelist_manager: Optional[WhitelistManager] = None):
        self.whitelist_manager = whitelist_manager or WhitelistManager()

    async def verify(
        self,
        law_name: str,
        article_num: int,
        cited_content: Optional[str] = None
    ) -> RegulationResult:
        """三级核实流程"""
        result = RegulationResult(
            is_valid=False,
            law_name=law_name,
            article_num=article_num
        )

        tier1_passed = await self._verify_law_exists(law_name)
        result.tier1_passed = tier1_passed
        result.law_exists = tier1_passed

        if not tier1_passed:
            result.reason = "WHITELIST_VIOLATION: Law not in whitelist"
            return result

        tier2_passed = await self._verify_article(law_name, article_num)
        result.tier2_passed = tier2_passed
        result.article_exists = tier2_passed

        if not tier2_passed:
            result.reason = "ARTICLE_OUT_OF_RANGE: Article number not valid"
            return result

        if cited_content:
            relevance_result = await self.verify_content_relevance(
                law_name, article_num, cited_content
            )
            result.tier3_score = relevance_result.score
            result.is_valid = relevance_result.is_valid
            result.reason = relevance_result.reason
        else:
            result.is_valid = tier1_passed and tier2_passed

        return result

    async def verify_citation(
        self,
        citation: str,
        context: str
    ) -> RegulationResult:
        """验证引用格式"""
        citation_stripped = citation.strip()

        for phrase in self.VAGUE_REFERENCE_PHRASES:
            if phrase in citation_stripped:
                return RegulationResult(
                    is_valid=False,
                    law_name="",
                    article_num=0,
                    reason=f"VAGUE_REFERENCE: '{phrase}' is too vague"
                )

        return RegulationResult(
            is_valid=True,
            law_name="",
            article_num=0
        )

    async def verify_content_relevance(
        self,
        law_name: str,
        article_num: int,
        cited_content: str
    ) -> ContentRelevanceResult:
        """Tier 3: 验证内容相关性"""
        score = self._calculate_content_similarity(cited_content, law_name, article_num)

        return ContentRelevanceResult(
            is_valid=score >= 0.5,
            score=score,
            reason="" if score >= 0.5 else "Content relevance too low"
        )

    async def _verify_law_exists(self, law_name: str) -> bool:
        """Tier 1: 验证法规存在"""
        await asyncio.sleep(0.001)
        return self.whitelist_manager.is_whitelisted(law_name)

    async def _verify_article(self, law_name: str, article_num: int) -> bool:
        """Tier 2: 验证条款存在"""
        await asyncio.sleep(0.001)
        return self.whitelist_manager.validate_article_number(law_name, article_num)

    def _calculate_content_similarity(
        self,
        cited_content: str,
        law_name: str,
        article_num: int
    ) -> float:
        """计算内容相似度 - 简化的相似度计算"""
        keywords = self._get_law_keywords(law_name, article_num)
        if not keywords:
            return 0.5

        content_lower = cited_content.lower()
        match_count = sum(1 for kw in keywords if kw.lower() in content_lower)

        return min(1.0, match_count / max(1, len(keywords)))

    def _get_law_keywords(self, law_name: str, article_num: int) -> List[str]:
        """获取法规条款关键词"""
        keyword_map = {
            "人工智能法": {
                28: ["算法", "备案", "人工智能企业", "模型", "人工智能", "企业", "应当"],
                15: ["数据", "保护", "个人信息"],
            },
            "数据安全法": {
                21: ["数据安全", "保护", "监管"],
                27: ["重要数据", "处理"],
            }
        }

        if law_name in keyword_map and article_num in keyword_map[law_name]:
            return keyword_map[law_name][article_num]

        return ["法规", "法律", "规定"]

    async def _get_article_content(self, law_name: str, article_num: int) -> Optional[str]:
        """获取条款内容"""
        await asyncio.sleep(0.001)
        return None
