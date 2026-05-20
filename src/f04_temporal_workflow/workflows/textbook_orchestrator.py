"""
全书编排工作流 - 教材编写全流程的 Temporal 编排器。

完整流程:
Phase 1: 提纲生成 → HUMAN_TASK 大纲审核
Phase 2: 并行章节编写 (Child Workflows)
Phase 3: 全量安全扫描
Phase 4: 全量质量评分
Phase 5: 风险分级 → HUMAN_TASK 最终审核
Phase 6: 输出汇总报告
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from .mock_client import (
    ActivityOptions,
    ChildWorkflowOptions,
    MockTemporalClient,
    RetryPolicy,
    SignalType,
    TemporalWorkflow,
    get_mock_client,
)
from .textbook_chapter import TextbookChapterWorkflow
from ..activities.content_generation import generate_chapter_outline
from ..activities.quality_check import batch_score_chapters
from ..activities.security_scan import batch_scan_chapters

logger = logging.getLogger(__name__)


class TextbookOrchestratorState:
    """全书编排状态机"""

    INIT = "INIT"
    OUTLINE_GENERATING = "OUTLINE_GENERATING"
    AWAITING_OUTLINE_REVIEW = "AWAITING_OUTLINE_REVIEW"
    CHAPTERS_WRITING = "CHAPTERS_WRITING"
    SECURITY_SCANNING = "SECURITY_SCANNING"
    QUALITY_SCORING = "QUALITY_SCORING"
    AWAITING_FINAL_REVIEW = "AWAITING_FINAL_REVIEW"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

    TRANSITIONS = {
        INIT: [OUTLINE_GENERATING],
        OUTLINE_GENERATING: [AWAITING_OUTLINE_REVIEW, CHAPTERS_WRITING],  # 允许跳过审核
        AWAITING_OUTLINE_REVIEW: [CHAPTERS_WRITING, FAILED, CANCELLED],
        CHAPTERS_WRITING: [SECURITY_SCANNING, FAILED],
        SECURITY_SCANNING: [QUALITY_SCORING, FAILED],
        QUALITY_SCORING: [AWAITING_FINAL_REVIEW, COMPLETED, FAILED],  # 允许跳过最终审核
        AWAITING_FINAL_REVIEW: [COMPLETED, FAILED, CANCELLED],
        COMPLETED: [],
        FAILED: [],
        CANCELLED: [],
    }


@TemporalWorkflow.defn(name="TextbookOrchestratorWorkflow")
class TextbookOrchestratorWorkflow:
    """
    教材编写全流程编排工作流

    协调多个 ChapterWorkflow 的并行执行，管理整体质量门控和审核流程。
    """

    def __init__(self):
        self._temporal_client: Optional[MockTemporalClient] = None
        self._context = None
        self._state = TextbookOrchestratorState.INIT
        self._chapter_results: List[Dict[str, Any]] = []
        self._batch_scan_result: Optional[Dict[str, Any]] = None
        self._batch_quality_result: Optional[List[Dict[str, Any]]] = None

    def _transition(self, new_state: str):
        """状态转换"""
        allowed = TextbookOrchestratorState.TRANSITIONS.get(self._state, [])
        if new_state not in allowed:
            raise RuntimeError(
                f"Invalid state transition: {self._state} → {new_state}. Allowed: {allowed}"
            )
        logger.info(f"[Orchestrator] State: {self._state} → {new_state}")
        self._state = new_state

    async def execute(
        self,
        textbook_id: str,
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        执行全书编排工作流

        Args:
            textbook_id: 教材唯一标识
            config: 教材配置
                {
                    "title": str,
                    "subject": str,
                    "grade_level": str,
                    "chapters": [
                        {
                            "chapter_id": str,
                            "title": str,
                            "order": int,
                            "learning_objectives": List[str],
                            "review_required": bool (default True),
                            "max_rewrites": int (default 3),
                        },
                        ...
                    ],
                    "outline_review_required": bool (default True),
                    "final_review_required": bool (default True),
                    "quality_threshold": float (default 70.0),
                    "parallel_chapter_limit": int (default 5),
                }

        Returns:
            {
                "textbook_id": str,
                "status": "COMPLETED" | "NEEDS_REVIEW" | "FAILED",
                "outline": Dict,
                "chapters": List[Dict],
                "security_scan": Dict,
                "quality_scores": Dict,
                "summary_report": Dict,
            }
        """
        client = self._temporal_client or get_mock_client()
        workflow_id = self._context.workflow_id if self._context else "unknown"

        title = config.get("title", "Untitled Textbook")
        subject = config.get("subject", "低空经济")
        chapters_config = config.get("chapters", [])
        outline_review_required = config.get("outline_review_required", True)
        final_review_required = config.get("final_review_required", True)
        quality_threshold = config.get("quality_threshold", 70.0)
        parallel_limit = config.get("parallel_chapter_limit", 5)

        logger.info(
            f"[Orchestrator:{textbook_id}] Starting textbook workflow: {title} "
            f"({len(chapters_config)} chapters)"
        )
        self._transition(TextbookOrchestratorState.OUTLINE_GENERATING)

        # ── Phase 1: 生成全书提纲 ────────────────────────────────────
        logger.info(f"[Orchestrator:{textbook_id}] Phase 1: Generating textbook outline")

        book_learning_objectives = []
        for ch in chapters_config:
            book_learning_objectives.extend(ch.get("learning_objectives", []))

        outline_result = await client.execute_activity(
            generate_chapter_outline,
            chapter_id=f"book-{textbook_id}",
            title=f"全书提纲: {title}",
            learning_objectives=book_learning_objectives[:20],  # Trim to top 20
            options=ActivityOptions(
                task_queue="textbook-writing-queue",
                start_to_close_timeout_seconds=120,
                retry_policy=RetryPolicy(max_attempts=2),
            ),
        )

        # ── Phase 2: HUMAN_TASK 大纲审核 ─────────────────────────────
        if outline_review_required:
            self._transition(TextbookOrchestratorState.AWAITING_OUTLINE_REVIEW)
            logger.info(f"[Orchestrator:{textbook_id}] Phase 2: Awaiting human outline review")

            signal = await client.wait_for_signal(
                workflow_id=workflow_id,
                signal_names=[
                    SignalType.HUMAN_REVIEW_APPROVE.value,
                    SignalType.HUMAN_REVIEW_REVISE.value,
                    SignalType.HUMAN_REVIEW_REJECT.value,
                ],
                timeout_seconds=86400,  # 24 hours for outline review
            )

            signal_type = signal["signal"]
            if signal_type == SignalType.HUMAN_REVIEW_REJECT.value:
                self._transition(TextbookOrchestratorState.FAILED)
                logger.warning(f"[Orchestrator:{textbook_id}] Outline rejected by human review")
                return {
                    "textbook_id": textbook_id,
                    "status": "REJECTED",
                    "rejection_reason": "Human reviewer rejected textbook outline",
                    "outline": outline_result,
                    "phase": "OUTLINE_REVIEW",
                }
            elif signal_type == SignalType.HUMAN_REVIEW_REVISE.value:
                logger.info(f"[Orchestrator:{textbook_id}] Outline needs revision, proceeding with caution")

        # ── Phase 3: 并行章节编写 ────────────────────────────────────
        self._transition(TextbookOrchestratorState.CHAPTERS_WRITING)
        logger.info(f"[Orchestrator:{textbook_id}] Phase 3: Writing chapters in parallel")

        # 分批并行执行 (受 parallel_limit 控制)
        chapter_results = []
        for batch_start in range(0, len(chapters_config), parallel_limit):
            batch = chapters_config[batch_start : batch_start + parallel_limit]
            logger.info(
                f"[Orchestrator:{textbook_id}] Writing chapter batch "
                f"{batch_start // parallel_limit + 1}: {len(batch)} chapters"
            )

            # 并行启动子工作流
            tasks = []
            for ch_config in batch:
                ch_config.setdefault("review_required", True)
                ch_config.setdefault("max_rewrites", 3)
                task = client.start_child_workflow(
                    TextbookChapterWorkflow,
                    ch_config,
                    book_subject=subject,
                    options=ChildWorkflowOptions(
                        task_queue="textbook-writing-queue",
                        workflow_id_suffix=f"ch-{ch_config.get('chapter_id', 'unknown')}",
                    ),
                )
                tasks.append(task)

            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, result in enumerate(batch_results):
                ch_config = batch[i]
                if isinstance(result, Exception):
                    logger.error(
                        f"[Orchestrator:{textbook_id}] Chapter "
                        f"'{ch_config.get('chapter_id')}' failed: {result}"
                    )
                    chapter_results.append({
                        "chapter_id": ch_config.get("chapter_id", "unknown"),
                        "status": "FAILED",
                        "error": str(result),
                    })
                else:
                    chapter_results.append(result)

            logger.info(f"[Orchestrator:{textbook_id}] Batch complete: {len(batch)} chapters processed")

        self._chapter_results = chapter_results

        # 检查是否有章节失败
        completed_chapters = [r for r in chapter_results if r.get("status") in ("COMPLETED", "NEEDS_REVIEW")]
        failed_chapters = [r for r in chapter_results if r.get("status") == "FAILED"]

        logger.info(
            f"[Orchestrator:{textbook_id}] Chapters: {len(completed_chapters)} completed, "
            f"{len(failed_chapters)} failed"
        )

        if not completed_chapters:
            self._transition(TextbookOrchestratorState.FAILED)
            return {
                "textbook_id": textbook_id,
                "status": "FAILED",
                "reason": "All chapters failed to generate",
                "chapters": chapter_results,
            }

        # ── Phase 4: 全量安全扫描 ────────────────────────────────────
        self._transition(TextbookOrchestratorState.SECURITY_SCANNING)
        logger.info(f"[Orchestrator:{textbook_id}] Phase 4: Batch security scanning")

        scan_input = [
            {
                "chapter_id": r["chapter_id"],
                "content": r.get("content", {}).get("content", ""),
            }
            for r in completed_chapters
        ]

        self._batch_scan_result = await client.execute_activity(
            batch_scan_chapters,
            scan_input,
            scan_level="STANDARD",
            options=ActivityOptions(
                task_queue="textbook-writing-queue",
                start_to_close_timeout_seconds=600,
                retry_policy=RetryPolicy(max_attempts=2),
            ),
        )

        # ── Phase 5: 全量质量评分 ────────────────────────────────────
        self._transition(TextbookOrchestratorState.QUALITY_SCORING)
        logger.info(f"[Orchestrator:{textbook_id}] Phase 5: Batch quality scoring")

        quality_input = [
            {
                "chapter_id": r["chapter_id"],
                "content": r.get("content", {}).get("content", ""),
            }
            for r in completed_chapters
        ]

        self._batch_quality_result = await client.execute_activity(
            batch_score_chapters,
            quality_input,
            options=ActivityOptions(
                task_queue="textbook-writing-queue",
                start_to_close_timeout_seconds=600,
                retry_policy=RetryPolicy(max_attempts=2),
            ),
        )

        # ── Phase 6: 风险分级 & 最终审核 ─────────────────────────────
        risk_assessment = self._assess_risk(completed_chapters, self._batch_quality_result)

        if final_review_required:
            self._transition(TextbookOrchestratorState.AWAITING_FINAL_REVIEW)
            logger.info(f"[Orchestrator:{textbook_id}] Phase 6: Awaiting final human review")

            signal = await client.wait_for_signal(
                workflow_id=workflow_id,
                signal_names=[
                    SignalType.HUMAN_REVIEW_APPROVE.value,
                    SignalType.HUMAN_REVIEW_REVISE.value,
                    SignalType.HUMAN_REVIEW_REJECT.value,
                ],
                timeout_seconds=86400,  # 24 hours
            )

            signal_type = signal["signal"]
            if signal_type == SignalType.HUMAN_REVIEW_REJECT.value:
                self._transition(TextbookOrchestratorState.FAILED)
                return {
                    "textbook_id": textbook_id,
                    "status": "REJECTED",
                    "rejection_reason": "Human reviewer rejected final textbook",
                    "chapters": chapter_results,
                    "risk_assessment": risk_assessment,
                    "phase": "FINAL_REVIEW",
                }

        # ── Phase 7: 汇总输出 ────────────────────────────────────────
        self._transition(TextbookOrchestratorState.COMPLETED)

        summary = self._build_summary(
            textbook_id=textbook_id,
            title=title,
            subject=subject,
            outline=outline_result,
            chapters=chapter_results,
            scan_result=self._batch_scan_result,
            quality_result=self._batch_quality_result,
            risk_assessment=risk_assessment,
        )

        logger.info(f"[Orchestrator:{textbook_id}] COMPLETED: {summary['summary']['overall_grade']}")
        return summary

    def _assess_risk(
        self,
        chapters: List[Dict[str, Any]],
        quality_results: Optional[List[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        """风险评估"""
        risks = []
        overall_risk = "LOW"

        if quality_results:
            for qr in quality_results:
                if qr.get("grade") in ("C", "D"):
                    risks.append({
                        "chapter_id": qr["chapter_id"],
                        "type": "LOW_QUALITY",
                        "severity": "HIGH" if qr.get("grade") == "D" else "MEDIUM",
                        "detail": f"Chapter scored grade {qr['grade']} ({qr['overall_score']})",
                    })

        if self._batch_scan_result:
            for v in self._batch_scan_result.get("violations", []):
                risks.append({
                    "chapter_id": v.get("chapter_id", ""),
                    "type": "SECURITY_VIOLATION",
                    "severity": v.get("severity", "MEDIUM"),
                    "detail": v.get("rule_name", "Security violation found"),
                })

        # 计算整体风险级别
        severity_scores = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
        max_severity = 0
        for risk in risks:
            max_severity = max(max_severity, severity_scores.get(risk["severity"], 0))

        if max_severity >= 3:
            overall_risk = "CRITICAL"
        elif max_severity >= 2:
            overall_risk = "HIGH"
        elif max_severity >= 1:
            overall_risk = "MEDIUM"

        return {
            "overall_risk": overall_risk,
            "risks": risks,
            "risk_count": len(risks),
        }

    def _build_summary(
        self,
        textbook_id: str,
        title: str,
        subject: str,
        outline: Dict[str, Any],
        chapters: List[Dict[str, Any]],
        scan_result: Optional[Dict[str, Any]],
        quality_result: Optional[List[Dict[str, Any]]],
        risk_assessment: Dict[str, Any],
    ) -> Dict[str, Any]:
        """构建最终输出报告"""
        completed = [c for c in chapters if c.get("status") in ("COMPLETED", "NEEDS_REVIEW")]
        failed = [c for c in chapters if c.get("status") == "FAILED"]

        # 计算平均质量分
        avg_score = 0
        if quality_result:
            scores = [r["overall_score"] for r in quality_result]
            avg_score = sum(scores) / len(scores) if scores else 0

        # 确定总体等级
        if avg_score >= 85:
            overall_grade = "A"
        elif avg_score >= 70:
            overall_grade = "B"
        elif avg_score >= 55:
            overall_grade = "C"
        else:
            overall_grade = "D"

        scan_status = scan_result.get("status", "UNKNOWN") if scan_result else "NOT_SCANNED"

        return {
            "textbook_id": textbook_id,
            "title": title,
            "subject": subject,
            "status": "COMPLETED",
            "outline": outline,
            "chapters": chapters,
            "security_scan": scan_result,
            "quality_scores": quality_result,
            "risk_assessment": risk_assessment,
            "summary": {
                "total_chapters": len(chapters),
                "completed_chapters": len(completed),
                "failed_chapters": len(failed),
                "average_quality_score": round(avg_score, 1),
                "overall_grade": overall_grade,
                "security_scan_status": scan_status,
                "overall_risk": risk_assessment["overall_risk"],
                "total_risk_issues": risk_assessment["risk_count"],
            },
            "message": (
                f"Textbook '{title}' generated successfully with "
                f"{len(completed)}/{len(chapters)} chapters (Grade: {overall_grade})"
            ),
        }
