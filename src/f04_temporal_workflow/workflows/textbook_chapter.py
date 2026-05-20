"""
章节编写工作流 - 单章节内容生成的完整 Temporal 工作流。

工作流步骤:
1. 生成章节提纲 (Activity: GenerateChapterOutline)
2. HUMAN_TASK: 人工审核提纲 (Signal: OUTLINE_REVIEW)
3. 生成章节内容 (Activity: GenerateChapterContent)
4. 质量评分 (Activity: ScoreChapterQuality)
5. 安全扫描 (Activity: ScanChapter)
6. 根据评分决定重试或完成
"""

import logging
from typing import Any, Dict, List, Optional

from .mock_client import (
    ActivityOptions,
    MockTemporalClient,
    RetryPolicy,
    SignalType,
    TemporalWorkflow,
    get_mock_client,
)
from ..activities.content_generation import generate_chapter_content, generate_chapter_outline
from ..activities.quality_check import score_chapter_quality
from ..activities.security_scan import scan_chapter

logger = logging.getLogger(__name__)


@TemporalWorkflow.defn(name="TextbookChapterWorkflow")
class TextbookChapterWorkflow:
    """
    章节编写工作流

    负责单个教材章节的完整生成流程: 提纲 → 审核 → 写作 → 评分 → 扫描
    """

    def __init__(self):
        self._temporal_client: Optional[MockTemporalClient] = None
        self._context = None

    async def execute(
        self,
        chapter_config: Dict[str, Any],
        book_subject: str = "低空经济",
    ) -> Dict[str, Any]:
        """
        执行章节编写工作流

        Args:
            chapter_config: 章节配置
                {
                    "chapter_id": str,
                    "title": str,
                    "order": int,
                    "learning_objectives": List[str],
                    "requirements": Optional[Dict],
                    "review_required": bool,
                    "max_rewrites": int
                }
            book_subject: 教材主题

        Returns:
            {
                "chapter_id": str,
                "status": "COMPLETED" | "FAILED" | "NEEDS_REVIEW",
                "content": Dict,
                "outline": Dict,
                "quality": Dict,
                "security": Dict,
                "rewrite_count": int,
            }
        """
        client = self._temporal_client or get_mock_client()
        workflow_id = self._context.workflow_id if self._context else "unknown"

        chapter_id = chapter_config["chapter_id"]
        title = chapter_config["title"]
        review_required = chapter_config.get("review_required", True)
        max_rewrites = chapter_config.get("max_rewrites", 3)
        requirements = chapter_config.get("requirements", {})

        logger.info(f"[ChapterWorkflow:{chapter_id}] Starting chapter workflow: {title}")

        rewrite_count = 0
        content_result: Optional[Dict[str, Any]] = None
        outline_result: Optional[Dict[str, Any]] = None
        quality_result: Optional[Dict[str, Any]] = None
        security_result: Optional[Dict[str, Any]] = None

        # ── Step 1: 生成章节提纲 ─────────────────────────────────────
        logger.info(f"[ChapterWorkflow:{chapter_id}] Step 1: Generating outline")

        outline_result = await client.execute_activity(
            generate_chapter_outline,
            chapter_id=chapter_id,
            title=title,
            learning_objectives=chapter_config.get("learning_objectives", [f"理解{book_subject}的核心概念"]),
            options=ActivityOptions(
                task_queue="textbook-writing-queue",
                start_to_close_timeout_seconds=60,
                retry_policy=RetryPolicy(max_attempts=2),
            ),
        )

        # ── Step 2: HUMAN_TASK 提纲审核 ───────────────────────────────
        if review_required:
            logger.info(f"[ChapterWorkflow:{chapter_id}] Step 2: Waiting for human outline review")

            signal = await client.wait_for_signal(
                workflow_id=workflow_id,
                signal_names=[
                    SignalType.HUMAN_REVIEW_APPROVE.value,
                    SignalType.HUMAN_REVIEW_REVISE.value,
                    SignalType.HUMAN_REVIEW_REJECT.value,
                ],
                timeout_seconds=3600,  # 1 hour timeout for human review
            )

            signal_type = signal["signal"]
            if signal_type == SignalType.HUMAN_REVIEW_REJECT.value:
                logger.warning(f"[ChapterWorkflow:{chapter_id}] Outline rejected by human review")
                return {
                    "chapter_id": chapter_id,
                    "status": "REJECTED",
                    "rejection_reason": "Human reviewer rejected chapter outline",
                    "outline": outline_result,
                }
            elif signal_type == SignalType.HUMAN_REVIEW_REVISE.value:
                logger.info(f"[ChapterWorkflow:{chapter_id}] Outline requires revision")
                # 标记需要修改，但在 mock 中继续

        # ── Step 3: 生成章节内容 (支持重写) ──────────────────────────
        while rewrite_count <= max_rewrites:
            logger.info(
                f"[ChapterWorkflow:{chapter_id}] Step 3: Generating content (attempt {rewrite_count + 1})"
            )

            content_result = await client.execute_activity(
                generate_chapter_content,
                chapter_id=chapter_id,
                title=title,
                subject=book_subject,
                requirements=requirements,
                options=ActivityOptions(
                    task_queue="textbook-writing-queue",
                    start_to_close_timeout_seconds=300,
                    retry_policy=RetryPolicy(max_attempts=3, initial_interval_seconds=2),
                    idempotency_key=f"content-{chapter_id}-attempt-{rewrite_count}",
                ),
            )

            # ── Step 4: 质量评分 ─────────────────────────────────────
            logger.info(f"[ChapterWorkflow:{chapter_id}] Step 4: Quality scoring")

            quality_result = await client.execute_activity(
                score_chapter_quality,
                chapter_id=chapter_id,
                content=content_result["content"],
                options=ActivityOptions(
                    task_queue="textbook-writing-queue",
                    start_to_close_timeout_seconds=120,
                    retry_policy=RetryPolicy(max_attempts=2),
                ),
            )

            # 检查是否需要重写
            if quality_result["grade"] in ("A", "B"):
                logger.info(
                    f"[ChapterWorkflow:{chapter_id}] Quality passed (Grade: {quality_result['grade']})"
                )
                break

            rewrite_count += 1
            if rewrite_count <= max_rewrites:
                logger.warning(
                    f"[ChapterWorkflow:{chapter_id}] Quality insufficient "
                    f"(Grade: {quality_result['grade']}), rewriting... (attempt {rewrite_count})"
                )
                # 给 AI 更好的提示
                requirements["improvement_hints"] = quality_result.get("issues", [])
            else:
                logger.error(
                    f"[ChapterWorkflow:{chapter_id}] Max rewrites ({max_rewrites}) reached with grade {quality_result['grade']}"
                )

        # ── Step 5: 安全扫描 ─────────────────────────────────────────
        logger.info(f"[ChapterWorkflow:{chapter_id}] Step 5: Security scanning")

        security_result = await client.execute_activity(
            scan_chapter,
            chapter_id=chapter_id,
            content=content_result["content"],
            scan_level="STANDARD",
            options=ActivityOptions(
                task_queue="textbook-writing-queue",
                start_to_close_timeout_seconds=120,
                retry_policy=RetryPolicy(max_attempts=2),
            ),
        )

        # ── 汇总结果 ──────────────────────────────────────────────────
        final_status = "COMPLETED"
        if security_result["status"] == "FAIL":
            final_status = "NEEDS_REVIEW"
        elif quality_result["grade"] in ("C", "D"):
            final_status = "NEEDS_REVIEW"

        result = {
            "chapter_id": chapter_id,
            "status": final_status,
            "outline": outline_result,
            "content": content_result,
            "quality": quality_result,
            "security": security_result,
            "rewrite_count": rewrite_count,
            "message": (
                f"Chapter completed with grade {quality_result['grade']}"
                if final_status == "COMPLETED"
                else f"Chapter needs review - quality grade {quality_result['grade']}"
            ),
        }

        logger.info(f"[ChapterWorkflow:{chapter_id}] Completed: {result['message']}")
        return result

    async def on_signal(self, signal_name: str, payload: Any = None) -> None:
        """处理外部信号"""
        logger.info(f"[ChapterWorkflow] Received signal '{signal_name}': {payload}")
