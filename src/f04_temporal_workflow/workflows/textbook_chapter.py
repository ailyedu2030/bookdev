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

import asyncio
import hashlib
import logging
import os
from typing import Any

from ..activities.content_generation import generate_chapter_content, generate_chapter_outline
from ..activities.quality_check import score_chapter_quality
from ..activities.security_scan import scan_chapter
from .mock_client import (
    ActivityOptions,
    MockTemporalClient,
    RetryPolicy,
    SignalType,
    TemporalQuery,
    TemporalWorkflow,
    get_mock_client,
)

logger = logging.getLogger(__name__)


# TEMP-023: 配置常量
DEFAULT_OUTLINE_TIMEOUT = int(os.environ.get("OUTLINE_REVIEW_TIMEOUT", "3600"))
DEFAULT_CONTENT_TIMEOUT = int(os.environ.get("CONTENT_TIMEOUT", "600"))


@TemporalWorkflow.defn(name="TextbookChapterWorkflow")
class TextbookChapterWorkflow:
    """
    章节编写工作流

    负责单个教材章节的完整生成流程: 提纲 → 审核 → 写作 → 评分 → 扫描
    """

    def __init__(self):
        self._temporal_client: MockTemporalClient | None = None
        self._context = None
        # TEMP-019: 状态持久化
        self._state: dict[str, Any] = {}
        # TEMP-016: 心跳计数
        self._heartbeat_count = 0

    async def execute(
        self,
        chapter_config: dict[str, Any],
        book_subject: str = "低空经济",
    ) -> dict[str, Any]:
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

        # TEMP-019: 从持久化存储恢复状态
        saved_state = await client.load_state(workflow_id)
        if saved_state and "_workflow_state" in saved_state:
            self._state = saved_state["_workflow_state"]
            logger.info(f"[ChapterWorkflow:{chapter_id}] Restored state from persistence")

        rewrite_count = self._state.get("rewrite_count", 0)
        content_result: dict[str, Any] | None = None
        outline_result: dict[str, Any] | None = None
        quality_result: dict[str, Any] | None = None
        security_result: dict[str, Any] | None = None

        # TEMP-016: 开始心跳
        asyncio.create_task(self._send_heartbeat_loop(workflow_id, chapter_id))

        try:
            # ── Step 1: 生成章节提纲 ─────────────────────────────────────
            logger.info(f"[ChapterWorkflow:{chapter_id}] Step 1: Generating outline")

            outline_result = await client.execute_activity(
                generate_chapter_outline,
                chapter_id=chapter_id,
                title=title,
                learning_objectives=chapter_config.get("learning_objectives", [f"理解{book_subject}的核心概念"]),
                options=ActivityOptions(
                    task_queue="textbook-writing-queue",
                    start_to_close_timeout_seconds=120,  # TEMP-005: 60->120
                    retry_policy=RetryPolicy(max_attempts=3),
                ),
            )

            # TEMP-019: 定期保存状态
            self._state["outline"] = outline_result
            await client.save_state(workflow_id, self._state)

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
                    timeout_seconds=DEFAULT_OUTLINE_TIMEOUT,  # TEMP-023: 从配置读取
                )

                # TEMP-009: 超时恢复机制
                if signal.get("signal") == "TIMEOUT":
                    logger.warning(f"[ChapterWorkflow:{chapter_id}] Outline review timed out, proceeding with caution")
                    # 可以选择继续、重试或终止
                    # 这里选择继续但标记需要后续审核
                    self._state["outline_needs_review"] = True

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
                logger.info(f"[ChapterWorkflow:{chapter_id}] Step 3: Generating content (attempt {rewrite_count + 1})")

                # TEMP-013: 使用内容哈希作为幂等性key，而不是尝试次数
                content_key = f"content-{chapter_id}-{hashlib.sha256(title.encode()).hexdigest()[:16]}"

                content_result = await client.execute_activity(
                    generate_chapter_content,
                    chapter_id=chapter_id,
                    title=title,
                    subject=book_subject,
                    requirements=requirements,
                    options=ActivityOptions(
                        task_queue="textbook-writing-queue",
                        start_to_close_timeout_seconds=DEFAULT_CONTENT_TIMEOUT,  # TEMP-004: 300->600
                        retry_policy=RetryPolicy(max_attempts=5, initial_interval_seconds=2),  # TEMP-001: 3->5
                        idempotency_key=content_key,
                        heartbeat_timeout_seconds=30,  # TEMP-016: 心跳
                    ),
                )

                # TEMP-019: 保存进度
                self._state["content"] = content_result
                self._state["rewrite_count"] = rewrite_count
                await client.save_state(workflow_id, self._state)

                # ── Step 4: 质量评分 ─────────────────────────────────────
                logger.info(f"[ChapterWorkflow:{chapter_id}] Step 4: Quality scoring")

                quality_result = await client.execute_activity(
                    score_chapter_quality,
                    chapter_id=chapter_id,
                    content=content_result["content"],
                    options=ActivityOptions(
                        task_queue="textbook-writing-queue",
                        start_to_close_timeout_seconds=120,
                        retry_policy=RetryPolicy(max_attempts=3),  # 增加重试
                    ),
                )

                # 检查是否需要重写
                if quality_result["grade"] in ("A", "B"):
                    logger.info(f"[ChapterWorkflow:{chapter_id}] Quality passed (Grade: {quality_result['grade']})")
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
                    retry_policy=RetryPolicy(max_attempts=3),
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

            # TEMP-019: 清理持久化状态
            self._state.clear()
            await client.save_state(workflow_id, {})

            logger.info(f"[ChapterWorkflow:{chapter_id}] Completed: {result['message']}")
            return result

        except Exception as e:
            logger.error(f"[ChapterWorkflow:{chapter_id}] Workflow failed: {e}")
            # TEMP-019: 保存错误状态
            self._state["error"] = str(e)
            self._state["failed_at"] = "content_generation" if content_result is None else "unknown"
            await client.save_state(workflow_id, self._state)
            raise

    # TEMP-016: 心跳循环
    async def _send_heartbeat_loop(self, workflow_id: str, chapter_id: str) -> None:
        """定期发送心跳"""
        client = self._temporal_client or get_mock_client()
        while True:
            await asyncio.sleep(30)
            try:
                self._heartbeat_count += 1
                await client.send_heartbeat(
                    f"workflow-{workflow_id}",
                    {
                        "chapter_id": chapter_id,
                        "heartbeat_count": self._heartbeat_count,
                        "workflow_id": workflow_id,
                    },
                )
                logger.debug(f"[ChapterWorkflow:{chapter_id}] Heartbeat #{self._heartbeat_count}")
            except Exception as e:
                logger.warning(f"[ChapterWorkflow:{chapter_id}] Heartbeat failed: {e}")
                break

    async def on_signal(self, signal_name: str, payload: Any = None) -> None:
        """处理外部信号"""
        logger.info(f"[ChapterWorkflow] Received signal '{signal_name}': {payload}")

    # TEMP-022: 查询处理器
    @TemporalQuery.defn(name="get_chapter_status")
    async def get_chapter_status(self) -> dict[str, Any]:
        """查询章节工作流状态"""
        return {
            "chapter_id": self._state.get("chapter_id", "unknown"),
            "status": "RUNNING" if self._context and self._context.status.value == "RUNNING" else "UNKNOWN",
            "rewrite_count": self._state.get("rewrite_count", 0),
            "has_outline": "outline" in self._state,
            "has_content": "content" in self._state,
            "heartbeat_count": self._heartbeat_count,
        }

    @TemporalQuery.defn(name="get_progress")
    async def get_progress(self) -> dict[str, Any]:
        """查询工作流进度"""
        progress = {
            "outline_generated": "outline" in self._state,
            "content_generated": "content" in self._state,
            "quality_scored": self._state.get("quality") is not None,
            "security_scanned": self._state.get("security") is not None,
            "rewrite_count": self._state.get("rewrite_count", 0),
        }
        total_steps = 5
        completed_steps = sum(1 for v in progress.values() if v)
        progress["percent_complete"] = round(completed_steps / total_steps * 100, 1)
        return progress
