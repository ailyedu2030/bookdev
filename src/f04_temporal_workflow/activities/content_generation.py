"""
内容生成活动 - 负责教材章节内容的 AI 生成。

支持:
- 单章生成 (幂等: 相同章节 ID 返回缓存结果)
- 批量生成
- 章节提纲生成
- 多模态内容生成 (文本/图表/公式)
"""

import hashlib
import logging
from typing import Any

from ..workflows.mock_client import TemporalActivity

logger = logging.getLogger(__name__)


# ─── Activity 函数 ─────────────────────────────────────────────────────────

@TemporalActivity.defn(
    name="GenerateChapterContent",
    idempotent=True,
)
async def generate_chapter_content(
    chapter_id: str,
    title: str,
    subject: str,
    requirements: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """生成单个章节的完整内容 (幂等)"""
    logger.info(f"[ContentGen] Generating chapter '{chapter_id}': {title}")

    # 模拟 AI 内容生成
    content = _build_chapter_content(chapter_id, title, subject, requirements or {})

    result = {
        "chapter_id": chapter_id,
        "title": title,
        "subject": subject,
        "content": content,
        "word_count": len(content.split()),
        "status": "GENERATED",
        "metadata": {
            "model": "mock-ai-model-v2",
            "generated_at": "2026-05-19T00:00:00Z",
            "requirements": requirements or {},
            "content_hash": hashlib.sha256(content.encode()).hexdigest()[:16],  # TEMP-013
        },
    }

    logger.info(f"[ContentGen] Chapter '{chapter_id}' generated ({result['word_count']} words)")
    return result


@TemporalActivity.defn(
    name="GenerateChapterOutline",
    idempotent=True,
)
async def generate_chapter_outline(
    chapter_id: str,
    title: str,
    learning_objectives: list[str],
) -> dict[str, Any]:
    """生成章节提纲 (幂等)"""
    logger.info(f"[ContentGen] Generating outline for chapter '{chapter_id}'")

    outline = []
    for i, obj in enumerate(learning_objectives, 1):
        outline.append({
            "section": f"{i}.{chr(96 + i)})",
            "heading": f"Section {i}: {obj[:60]}",
            "subsections": [
                f"Introduction to {obj[:40]}",
                f"Core Concepts of {obj[:40]}",
                "Practical Applications",
                "Summary and Review",
            ],
        })

    return {
        "chapter_id": chapter_id,
        "title": title,
        "outline": outline,
        "total_sections": len(outline),
        "estimated_hours": len(outline) * 0.5,
    }


@TemporalActivity.defn(
    name="BatchGenerateChapters",
    idempotent=True,
)
async def batch_generate_chapters(
    chapters: list[dict[str, Any]],
    textbook_subject: str,
) -> list[dict[str, Any]]:
    """
    批量生成章节内容 (幂等)
    TEMP-014: 现在使用基于内容哈希的幂等性key
    """
    logger.info(f"[ContentGen] Batch generating {len(chapters)} chapters")

    # TEMP-014: 为批量操作生成唯一幂等键
    batch_id = f"batch-{textbook_subject}-{len(chapters)}"
    chapter_ids = [ch.get("id", "unknown") for ch in chapters]
    batch_key = hashlib.sha256(f"{batch_id}:{','.join(chapter_ids)}".encode()).hexdigest()[:16]

    results = []
    for ch in chapters:
        # TEMP-013: 使用内容哈希作为幂等键的基础
        ch_id = ch.get("id", "unknown")
        ch_title = ch.get("title", "Untitled")
        hashlib.sha256(f"{ch_id}:{ch_title}".encode()).hexdigest()[:16]

        result = await generate_chapter_content(
            chapter_id=ch_id,
            title=ch_title,
            subject=textbook_subject,
            requirements=ch.get("requirements"),
        )
        # TEMP-014: 添加batch标识以便追踪
        result["batch_id"] = batch_key
        results.append(result)

    logger.info(f"[ContentGen] Batch complete: {len(results)} chapters, batch_key={batch_key[:16]}")
    return results


# ─── 内部内容构建 ──────────────────────────────────────────────────────────

def _build_chapter_content(
    chapter_id: str,
    title: str,
    subject: str,
    requirements: dict[str, Any],
) -> str:
    """构建章节内容 (模拟 AI 生成)"""

    sections = requirements.get("sections", 3)
    subsections_per = requirements.get("subsections", 3)

    content_parts = [
        f"# {title}\n",
        "## 学习目标\n",
        f"本章将介绍{subject}领域的核心概念和应用。通过本章学习，读者将能够：\n",
    ]

    for i in range(1, sections + 1):
        content_parts.append(f"\n## 第{i}节 {title} - 核心概念\n")
        for j in range(1, subsections_per + 1):
            content_parts.append(
                f"### {i}.{j} 要点讲解\n\n"
                f"在{subject}的框架下，本小节涵盖了以下关键内容：\n\n"
                f"- **理论基础**：建立{subject}的核心知识体系\n"
                f"- **实践应用**：通过案例分析展示实际应用场景\n"
                f"- **关联知识**：与前后章节的知识点进行连接\n\n"
            )

        content_parts.append(f"\n**本节目标**：掌握{subject}第{i}部分的核心概念\n")
        content_parts.append("\n**[思考题]**：如何将本节知识应用于实际场景？\n")

    content_parts.append("\n## 本章小结\n\n")
    content_parts.append(f"本章系统介绍了{title}的基础知识。下章将继续深入探讨相关主题。\n")
    content_parts.append("\n## 参考文献\n\n1. 教材编写组. (2026). 现代教材编写指南\n")

    return "\n".join(content_parts)


# ─── Activity 类 (用于工作流集成) ──────────────────────────────────────────

class ContentGeneration:
    """内容生成活动集合"""

    @staticmethod
    async def generate(chapter_id: str, title: str, subject: str, **kwargs) -> dict[str, Any]:
        return await generate_chapter_content(chapter_id, title, subject, kwargs)

    @staticmethod
    async def generate_outline(chapter_id: str, title: str, objectives: list[str]) -> dict[str, Any]:
        return await generate_chapter_outline(chapter_id, title, objectives)

    @staticmethod
    async def batch_generate(chapters: list[dict[str, Any]], subject: str) -> list[dict[str, Any]]:
        return await batch_generate_chapters(chapters, subject)
