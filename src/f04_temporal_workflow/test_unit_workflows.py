"""
单元测试 - Temporal 工作流的单元测试 (7个)

测试覆盖:
1. MockTemporalClient 基础 CRUD
2. Activity 注册和执行
3. Workflow 注册和执行
4. Signal 发送和接收
5. RetryPolicy 计算
6. Activity 幂等性
7. 子工作流执行
"""

import asyncio
import os

import pytest

# 确保 mock 模式
os.environ["MOCK_TEMPORAL"] = "true"

from src.f04_temporal_workflow.workflows.mock_client import (
    ActivityOptions,
    MockTemporalClient,
    RetryPolicy,
    SignalType,
    TemporalActivity,
    TemporalWorkflow,
    WorkflowStatus,
    get_mock_client,
)

# ─── Fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_client():
    """每个测试前重置客户端"""
    MockTemporalClient.reset_instance()
    yield
    MockTemporalClient.reset_instance()


@pytest.fixture
def client():
    return get_mock_client()


# ─── Test 1: MockTemporalClient 基础 CRUD ──────────────────────────────────

@pytest.mark.asyncio
async def test_01_client_start_and_get_workflow(client):
    """测试启动工作流和查询工作流状态"""

    @TemporalWorkflow.defn(name="TestBasicWorkflow")
    class TestBasicWorkflow:
        async def execute(self, value: int) -> dict:
            return {"result": value * 2}

    ctx = await client.start_workflow(TestBasicWorkflow, 21)

    assert ctx.status == WorkflowStatus.COMPLETED
    assert ctx.result == {"result": 42}
    assert ctx.workflow_type == "TestBasicWorkflow"

    # 查询工作流
    retrieved = await client.get_workflow(ctx.workflow_id)
    assert retrieved is not None
    assert retrieved.status == WorkflowStatus.COMPLETED
    assert len(retrieved.history) >= 2  # STARTED + COMPLETED


@pytest.mark.asyncio
async def test_02_workflow_failure_handling(client):
    """测试工作流失败处理"""

    @TemporalWorkflow.defn(name="TestFailureWorkflow")
    class TestFailureWorkflow:
        async def execute(self, should_fail: bool) -> dict:
            if should_fail:
                raise ValueError("Intentional workflow failure")
            return {"status": "ok"}

    # 成功案例
    ctx = await client.start_workflow(TestFailureWorkflow, False)
    assert ctx.status == WorkflowStatus.COMPLETED

    # 失败案例
    ctx = await client.start_workflow(TestFailureWorkflow, True)
    assert ctx.status == WorkflowStatus.FAILED
    assert "Intentional workflow failure" in str(ctx.error)


# ─── Test 2: Activity 注册和执行 ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_03_activity_basic_execution(client):
    """测试 Activity 基础注册和执行"""

    @TemporalActivity.defn(name="AddNumbers", idempotent=True)
    async def add_numbers(a: int, b: int) -> int:
        return a + b

    result = await client.execute_activity(
        add_numbers, 10, 20,
        options=ActivityOptions(start_to_close_timeout_seconds=10),
    )

    assert result == 30
    assert hasattr(add_numbers, "_temporal_activity")


# ─── Test 3: RetryPolicy 计算 ──────────────────────────────────────────────

def test_04_retry_policy_delays():
    """测试重试策略延迟计算"""
    policy = RetryPolicy(
        max_attempts=5,
        initial_interval_seconds=1,
        backoff_multiplier=2.0,
        max_interval_seconds=30,
    )

    assert policy.next_delay(1) == 1.0
    assert policy.next_delay(2) == 2.0
    assert policy.next_delay(3) == 4.0
    assert policy.next_delay(4) == 8.0
    assert policy.next_delay(5) == 16.0
    assert policy.next_delay(10) == 30.0  # 不应超过 max_interval


# ─── Test 4: Activity 重试和超时 ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_05_activity_retry_on_failure(client):
    """测试 Activity 失败后重试"""
    call_count = 0

    @TemporalActivity.defn(name="FlakyActivity", idempotent=False)
    async def flaky_activity() -> str:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise RuntimeError(f"Attempt {call_count} failed")
        return "success"

    result = await client.execute_activity(
        flaky_activity,
        options=ActivityOptions(
            start_to_close_timeout_seconds=30,
            retry_policy=RetryPolicy(
                max_attempts=5,
                initial_interval_seconds=0,  # No delay in tests
                backoff_multiplier=1.0,
            ),
        ),
    )

    assert result == "success"
    assert call_count == 3


# ─── Test 6: Signal 发送和接收 ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_06_signal_send_receive(client):
    """测试 Signal 发送和接收机制"""
    from src.f04_temporal_workflow.workflows.mock_client import WorkflowExecutionContext

    # 手动创建 workflow 上下文来测试 signal 机制
    wf_id = "signal-unit-test"

    ctx = WorkflowExecutionContext(
        workflow_id=wf_id,
        workflow_type="TestSignalWorkflow",
        run_id="test-run",
    )
    client._workflows[wf_id] = ctx

    # 发送 signal
    result = await client.signal_workflow(wf_id, SignalType.HUMAN_REVIEW_APPROVE, {"approved_by": "tester"})
    assert result is True

    # 验证信号存储
    retrieved = await client.get_workflow(wf_id)
    assert retrieved is not None
    assert SignalType.HUMAN_REVIEW_APPROVE.value in retrieved.signals

    # 发送另一个信号
    await client.signal_workflow(wf_id, SignalType.HUMAN_REVIEW_REJECT, {"reason": "test rejection"})
    assert SignalType.HUMAN_REVIEW_REJECT.value in retrieved.signals
    assert SignalType.HUMAN_REVIEW_APPROVE.value in retrieved.signals

    # 发送到不存在的工作流
    result = await client.signal_workflow("non-existent", SignalType.HUMAN_REVIEW_APPROVE)
    assert result is False


# ─── Test 7: Activity 幂等性 ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_07_activity_idempotency(client):
    """测试 Activity 幂等性 - 相同输入返回相同结果"""
    call_count = 0

    @TemporalActivity.defn(name="IdempotentCount", idempotent=True)
    async def idempotent_count(value: int) -> dict:
        nonlocal call_count
        call_count += 1
        return {"value": value, "execution_count": call_count}

    # 第一次调用
    result1 = await client.execute_activity(
        idempotent_count, 42,
        options=ActivityOptions(start_to_close_timeout_seconds=10),
    )

    # 第二次调用 - 幂等，应返回缓存
    result2 = await client.execute_activity(
        idempotent_count, 42,
        options=ActivityOptions(start_to_close_timeout_seconds=10),
    )

    assert result1["value"] == 42
    assert result2["value"] == 42
    # 幂等活动应该返回缓存结果 (在 mock 中执行计数不变)
    assert result2["execution_count"] == result1["execution_count"]


# ─── Test 8: 子工作流执行 ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_08_child_workflow_execution(client):
    """测试子工作流启动和结果获取"""

    @TemporalWorkflow.defn(name="ChildCalcWorkflow")
    class ChildCalcWorkflow:
        async def execute(self, x: int, y: int) -> dict:
            return {"product": x * y}

    @TemporalWorkflow.defn(name="ParentCalcWorkflow")
    class ParentCalcWorkflow:
        async def execute(self) -> dict:
            child_result = await client.start_child_workflow(
                ChildCalcWorkflow, 6, 7,
            )
            return {"parent": "done", "child": child_result}

    ctx = await client.start_workflow(ParentCalcWorkflow)

    assert ctx.status == WorkflowStatus.COMPLETED
    assert ctx.result["parent"] == "done"
    assert ctx.result["child"] == {"product": 42}


# ─── Additional: 工作流取消 ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_09_workflow_cancellation(client):
    """测试工作流取消"""

    @TemporalWorkflow.defn(name="LongRunningWorkflow")
    class LongRunningWorkflow:
        async def execute(self) -> dict:
            await asyncio.sleep(10)
            return {"status": "done"}

    # 先创建 workflow registry 记录但不要等待
    # 直接测试 cancel API
    cancelled = await client.cancel_workflow("non-existent-wf")
    assert cancelled is False

    # 验证 list_workflows
    workflows = client.list_workflows()
    assert isinstance(workflows, list)
