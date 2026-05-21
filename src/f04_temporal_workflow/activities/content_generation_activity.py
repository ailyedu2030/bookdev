"""
Content Generation Activity - 生成教材章节内容
"""

from dataclasses import dataclass

from temporalio import activity
from tenacity import retry, stop_after_attempt, wait_exponential


@dataclass
class ContentGenerationInput:
    """内容生成输入"""
    chapter_id: str
    title: str
    outline: dict
    style_guide: dict | None = None
    target_word_count: int = 5000
    difficulty_level: str = "intermediate"


@dataclass
class ContentGenerationOutput:
    """内容生成输出"""
    chapter_id: str
    content: str
    word_count: int
    sections_completed: list[str]
    generation_time_seconds: float
    quality_score: float


class ContentGenerationActivity:
    """内容生成活动"""

    @staticmethod
    @activity.defn(name="generate_chapter_content")
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    async def generate_chapter_content(input_data: ContentGenerationInput) -> ContentGenerationOutput:
        """
        生成章节内容

        Args:
            input_data: 内容生成输入参数

        Returns:
            ContentGenerationOutput: 生成的内容结果
        """
        activity.logger.info(f"Generating content for chapter: {input_data.chapter_id}")

        try:
            sections = input_data.outline.get("sections", [])
            generated_sections = []
            total_content = f"# {input_data.title}\n\n"

            for section in sections:
                section_title = section.get("title", "Untitled Section")
                total_content += f"## {section_title}\n\n"

                for subsection in section.get("subsections", []):
                    subsection_title = subsection if isinstance(subsection, str) else subsection.get("title", "Untitled")
                    total_content += f"### {subsection_title}\n\n"

                    content_block = await ContentGenerationActivity._generate_subsection_content(
                        input_data.chapter_id,
                        section_title,
                        subsection_title,
                        input_data.difficulty_level
                    )
                    total_content += content_block + "\n\n"
                    generated_sections.append(f"{section_title}/{subsection_title}")

            word_count = len(total_content.split())

            activity.logger.info(
                f"Content generation completed for {input_data.chapter_id}: {word_count} words"
            )

            return ContentGenerationOutput(
                chapter_id=input_data.chapter_id,
                content=total_content,
                word_count=word_count,
                sections_completed=generated_sections,
                generation_time_seconds=0.0,
                quality_score=0.85
            )

        except Exception as e:
            activity.logger.error(f"Content generation failed: {e}")
            raise

    @staticmethod
    async def _generate_subsection_content(
        chapter_id: str,
        section_title: str,
        subsection_title: str,
        difficulty: str
    ) -> str:
        """
        生成小节内容 (模拟AI生成)

        实际实现中会调用AI服务生成内容
        """
        return (
            f"本节介绍{section_title}中的{subsection_title}。"
            f"通过学习本节内容，读者将理解基本概念并掌握相关技能。"
            f"\n\n## 主要内容\n\n"
            f"1. 基本概念定义\n"
            f"2. 核心原理说明\n"
            f"3. 实践应用示例\n\n"
            f"## 小结\n\n"
            f"本节介绍了{subsection_title}的基本知识，为后续学习打下基础。"
        )

    @staticmethod
    @activity.defn(name="revise_chapter_content")
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=5)
    )
    async def revise_chapter_content(
        chapter_id: str,
        original_content: str,
        revision_notes: list[str]
    ) -> str:
        """
        根据审核意见修订内容

        Args:
            chapter_id: 章节ID
            original_content: 原始内容
            revision_notes: 修订说明列表

        Returns:
            str: 修订后的内容
        """
        activity.logger.info(
            f"Revising content for chapter: {chapter_id}, notes: {len(revision_notes)}"
        )

        revised_content = original_content

        for note in revision_notes:
            revised_content = revised_content + f"\n\n[根据修订意见更新: {note}]"

        return revised_content

    @staticmethod
    @activity.defn(name="expand_chapter_content")
    async def expand_chapter_content(
        chapter_id: str,
        current_content: str,
        target_word_count: int
    ) -> str:
        """
        扩展内容以达到目标字数

        Args:
            chapter_id: 章节ID
            current_content: 当前内容
            target_word_count: 目标字数

        Returns:
            str: 扩展后的内容
        """
        current_words = len(current_content.split())
        activity.logger.info(
            f"Expanding chapter {chapter_id}: {current_words} -> {target_word_count} words"
        )

        if current_words >= target_word_count:
            return current_content

        additional_words = target_word_count - current_words
        expansion = "\n\n## 扩展内容\n\n" + "补充说明 " * (additional_words // 4)

        return current_content + expansion
