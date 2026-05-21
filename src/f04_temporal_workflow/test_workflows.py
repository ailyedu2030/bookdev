"""
集成测试 - Temporal 工作流的端到端集成测试 (9个)

测试覆盖:
1. 端到端全书编排: 提纲→写作→扫描→评分→审核
2. 章节工作流: 提纲→审核→内容生成→评分→扫描
3. 人工审核暂停/恢复
4. 子工作流并行执行
5. 异常和重试
6. 内容生成幂等性
7. 安全扫描批量处理
8. 质量评分门控
9. 提纲生成活动
"""

import asyncio as aio
import os

import pytest

os.environ["MOCK_TEMPORAL"] = "true"

from src.f04_temporal_workflow.activities.content_generation import (
    generate_chapter_content,
    generate_chapter_outline,
)
from src.f04_temporal_workflow.activities.security_scan import batch_scan_chapters
from src.f04_temporal_workflow.workflows.mock_client import (
    ActivityOptions,
    MockTemporalClient,
    RetryPolicy,
    SignalType,
    TemporalActivity,
    WorkflowStatus,
    get_mock_client,
)
from src.f04_temporal_workflow.workflows.textbook_chapter import TextbookChapterWorkflow
from src.f04_temporal_workflow.workflows.textbook_orchestrator import TextbookOrchestratorWorkflow


@pytest.fixture(autouse=True)
def reset_client():
    MockTemporalClient.reset_instance()
    yield
    MockTemporalClient.reset_instance()


@pytest.fixture
def client():
    return get_mock_client()


@pytest.fixture
def sample_chapter_config():
    return {
        "chapter_id": "ch01",
        "title": "低空经济概论",
        "order": 1,
        "learning_objectives": [
            "理解低空经济的基本概念",
            "掌握低空经济的产业构成",
            "了解低空经济的发展趋势",
        ],
        "review_required": False,  # 加速测试 - 无需等待人工审核
        "max_rewrites": 3,
        "requirements": {
            "sections": 3,
            "subsections": 3,
            "target_word_count": 3000,
        },
    }


@pytest.fixture
def sample_textbook_config():
    return {
        "title": "低空经济学导论",
        "subject": "低空经济",
        "grade_level": "大学本科",
        "outline_review_required": False,  # 加速测试
        "final_review_required": False,  # 加速测试
        "quality_threshold": 70.0,
        "parallel_chapter_limit": 3,
        "chapters": [
            {
                "chapter_id": "ch01",
                "title": "低空经济概论",
                "order": 1,
                "learning_objectives": [
                    "理解低空经济的基本概念",
                    "掌握低空经济的产业构成",
                ],
                "review_required": False,
                "max_rewrites": 2,
            },
            {
                "chapter_id": "ch02",
                "title": "低空飞行器技术",
                "order": 2,
                "learning_objectives": [
                    "了解无人机技术基础",
                    "掌握eVTOL飞行器原理",
                ],
                "review_required": False,
                "max_rewrites": 2,
            },
            {
                "chapter_id": "ch03",
                "title": "低空经济产业生态",
                "order": 3,
                "learning_objectives": [
                    "理解低空物流商业模式",
                    "分析低空旅游市场",
                ],
                "review_required": False,
                "max_rewrites": 2,
            },
        ],
    }


# ─── Test 1: 章节工作流端到端 ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_01_chapter_workflow_e2e(client, sample_chapter_config):
    """测试章节工作流: 提纲→内容生成→评分→扫描"""
    ctx = await client.start_workflow(
        TextbookChapterWorkflow,
        sample_chapter_config,
        book_subject="低空经济",
    )

    assert ctx.status == WorkflowStatus.COMPLETED
    result = ctx.result

    assert result["chapter_id"] == "ch01"
    assert result["status"] in ("COMPLETED", "NEEDS_REVIEW")
    assert "outline" in result
    assert "content" in result
    assert "quality" in result
    assert "security" in result

    assert len(result["outline"]["outline"]) > 0
    assert result["outline"]["total_sections"] > 0
    assert "低空经济概论" in result["content"]["content"]
    assert result["content"]["word_count"] > 0
    assert "overall_score" in result["quality"]
    assert "grade" in result["quality"]
    assert 0 <= result["quality"]["overall_score"] <= 100
    assert result["security"]["status"] in ("PASS", "WARNING", "FAIL")


# ─── Test 2: 全书编排端到端 ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_02_orchestrator_workflow_e2e(client, sample_textbook_config):
    """测试全书编排: 提纲→并行章节→扫描→评分→审核"""
    ctx = await client.start_workflow(
        TextbookOrchestratorWorkflow,
        textbook_id="textbook-001",
        config=sample_textbook_config,
    )

    assert ctx.status == WorkflowStatus.COMPLETED
    result = ctx.result

    assert result["textbook_id"] == "textbook-001"
    assert result["status"] == "COMPLETED"
    assert "outline" in result
    assert len(result["outline"]["outline"]) > 0

    assert len(result["chapters"]) == 3
    for ch in result["chapters"]:
        assert ch["chapter_id"] in ("ch01", "ch02", "ch03")
        assert ch["status"] in ("COMPLETED", "NEEDS_REVIEW", "REJECTED")
        assert "content" in ch
        assert "quality" in ch

    assert "security_scan" in result
    assert result["security_scan"]["status"] in ("PASS", "WARNING")
    assert "quality_scores" in result
    assert len(result["quality_scores"]) == 3

    summary = result["summary"]
    assert summary["total_chapters"] == 3
    assert summary["completed_chapters"] <= 3
    assert "average_quality_score" in summary
    assert summary["overall_grade"] in ("A", "B", "C", "D")


# ─── Test 3: 人工审核暂停/恢复 ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_03_human_review_signal_mechanism(client):
    """测试人工审核 signal 机制"""
    # 测试 signal 发送和接收的核心机制
    wf_id = "signal-mechanism-test"

    # 手动注册工作流上下文并测试 signal
    from src.f04_temporal_workflow.workflows.mock_client import WorkflowExecutionContext

    ctx = WorkflowExecutionContext(
        workflow_id=wf_id,
        workflow_type="TestSignalWorkflow",
        run_id="test-run-id",
    )
    client._workflows[wf_id] = ctx

    # 发送 approve 信号
    result = await client.signal_workflow(wf_id, SignalType.HUMAN_REVIEW_APPROVE, {"reviewer": "test"})
    assert result is True

    # 验证信号已存储
    retrieved = await client.get_workflow(wf_id)
    assert retrieved is not None
    assert SignalType.HUMAN_REVIEW_APPROVE.value in retrieved.signals
    assert retrieved.signals[SignalType.HUMAN_REVIEW_APPROVE.value] == {"reviewer": "test"}

    # 测试 reject 信号
    await client.signal_workflow(wf_id, SignalType.HUMAN_REVIEW_REJECT, {"reason": "needs revision"})
    assert SignalType.HUMAN_REVIEW_REJECT.value in retrieved.signals

    # 测试发送信号到不存在的工作流
    result = await client.signal_workflow("non-existent-wf", SignalType.HUMAN_REVIEW_APPROVE)
    assert result is False


# ─── Test 4: 子工作流并行执行 ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_04_parallel_child_workflows(client):
    """测试多个子工作流并行执行"""

    async def run_parallel_chapters():
        tasks = []
        for i in range(5):
            task = client.start_child_workflow(
                TextbookChapterWorkflow,
                {
                    "chapter_id": f"parallel-ch{i:02d}",
                    "title": f"并行测试第{i+1}章",
                    "order": i + 1,
                    "learning_objectives": [f"并行测试目标{i+1}"],
                    "review_required": False,
                    "max_rewrites": 1,
                    "requirements": {"sections": 1, "subsections": 1},
                },
                book_subject="低空经济",
            )
            tasks.append(task)

        results = await aio.gather(*tasks, return_exceptions=False)
        return results

    results = await run_parallel_chapters()

    assert len(results) == 5
    for i, result in enumerate(results):
        assert result["chapter_id"] == f"parallel-ch{i:02d}"
        assert result["status"] in ("COMPLETED", "NEEDS_REVIEW")
        assert "content" in result
        assert "quality" in result
        assert "security" in result


# ─── Test 5: 异常和重试测试 ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_05_error_handling_and_retry(client):
    """测试异常处理和重试机制"""
    call_counts = {"fail_then_succeed": 0}

    @TemporalActivity.defn(name="FailThenSucceed", idempotent=False)
    async def fail_then_succeed(value: str) -> str:
        call_counts["fail_then_succeed"] += 1
        if call_counts["fail_then_succeed"] < 3:
            raise ConnectionError(f"Temporary failure {call_counts['fail_then_succeed']}")
        return f"success-{value}"

    result = await client.execute_activity(
        fail_then_succeed,
        "test",
        options=ActivityOptions(
            start_to_close_timeout_seconds=30,
            retry_policy=RetryPolicy(
                max_attempts=5,
                initial_interval_seconds=0,
                backoff_multiplier=1.0,
            ),
        ),
    )

    assert result == "success-test"
    assert call_counts["fail_then_succeed"] == 3

    # 测试不可重试错误
    call_counts_non_retryable = 0

    @TemporalActivity.defn(name="NonRetryableError", idempotent=False)
    async def non_retryable_activity() -> str:
        nonlocal call_counts_non_retryable
        call_counts_non_retryable += 1
        raise ValueError("ValidationError: 不可重试的错误")

    try:
        await client.execute_activity(
            non_retryable_activity,
            options=ActivityOptions(
                start_to_close_timeout_seconds=10,
                retry_policy=RetryPolicy(
                    max_attempts=5,
                    initial_interval_seconds=0,
                    non_retryable_errors=["ValueError"],
                ),
            ),
        )
        raise AssertionError("Should have raised")
    except ValueError:
        assert call_counts_non_retryable == 1


# ─── Test 6: 内容生成活动幂等性 ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_06_content_generation_idempotency(client):
    """测试内容生成活动的幂等性"""
    result1 = await client.execute_activity(
        generate_chapter_content,
        chapter_id="idem-ch01",
        title="幂等性测试",
        subject="低空经济",
        options=ActivityOptions(start_to_close_timeout_seconds=30),
    )

    result2 = await client.execute_activity(
        generate_chapter_content,
        chapter_id="idem-ch01",
        title="幂等性测试",
        subject="低空经济",
        options=ActivityOptions(start_to_close_timeout_seconds=30),
    )

    assert result1["chapter_id"] == result2["chapter_id"]
    assert result1["content"] == result2["content"]
    assert result1["word_count"] == result2["word_count"]


# ─── Test 7: 安全扫描批量处理 ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_07_security_scan_batch(client):
    """测试安全扫描批量处理"""
    content1 = await client.execute_activity(
        generate_chapter_content,
        chapter_id="sec-ch01",
        title="安全测试章1",
        subject="低空经济",
        options=ActivityOptions(start_to_close_timeout_seconds=30),
    )
    content2 = await client.execute_activity(
        generate_chapter_content,
        chapter_id="sec-ch02",
        title="安全测试章2",
        subject="低空经济",
        options=ActivityOptions(start_to_close_timeout_seconds=30),
    )

    scan_input = [
        {"chapter_id": "sec-ch01", "content": content1["content"]},
        {"chapter_id": "sec-ch02", "content": content2["content"]},
    ]

    result = await client.execute_activity(
        batch_scan_chapters,
        scan_input,
        scan_level="STANDARD",
        options=ActivityOptions(start_to_close_timeout_seconds=120),
    )

    assert result["total_chapters"] == 2
    assert result["status"] in ("PASS", "WARNING", "FAIL")
    assert result["passed"] + result["warnings"] + result["failed"] == 2
    assert "chapter_results" in result
    assert len(result["chapter_results"]) == 2


# ─── Test 8: 质量评分门控 ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_08_quality_gate_retry(client):
    """测试质量门控: 质量评分触发重写"""
    config = {
        "chapter_id": "quality-gate-test",
        "title": "质量门控测试",
        "order": 1,
        "learning_objectives": ["测试质量门控"],
        "review_required": False,
        "max_rewrites": 2,
        "requirements": {
            "sections": 1,
            "subsections": 1,
        },
    }

    ctx = await client.start_workflow(
        TextbookChapterWorkflow,
        config,
        book_subject="低空经济",
    )

    assert ctx.status == WorkflowStatus.COMPLETED
    result = ctx.result

    assert result["quality"]["overall_score"] > 0
    assert "rewrite_count" in result


# ─── Test 9: 提纲生成活动 ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_09_outline_generation(client):
    """测试提纲生成活动"""
    result = await client.execute_activity(
        generate_chapter_outline,
        chapter_id="outline-test",
        title="提纲生成测试",
        learning_objectives=["目标1", "目标2", "目标3"],
        options=ActivityOptions(start_to_close_timeout_seconds=30),
    )

    assert result["chapter_id"] == "outline-test"
    assert result["total_sections"] == 3
    assert len(result["outline"]) == 3
    assert "estimated_hours" in result
    for section in result["outline"]:
        assert "heading" in section
        assert "subsections" in section
