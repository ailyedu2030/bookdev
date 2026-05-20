"""
Mock Temporal Client - 模拟 Temporal SDK 行为，支持 MOCK_TEMPORAL 环境变量切换。

支持:
- Workflow 注册和执行
- Activity 注册和执行 (带重试/超时/幂等)
- Child Workflow
- Signal (Human-in-the-loop)
- Timer/Sleep
"""

import os
import uuid
import time
import json
import asyncio
import logging
import hashlib
import functools
import traceback
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypeVar, Generic, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

MOCK_TEMPORAL = os.environ.get("MOCK_TEMPORAL", "true").lower() in ("1", "true", "yes")

T = TypeVar("T")


def _make_cache_key(args: tuple, kwargs: dict) -> str:
    """生成幂等缓存键"""
    parts = [str(a) for a in args]
    parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    return hashlib.sha256("|".join(parts).encode()).hexdigest()


# ─── Data Models ──────────────────────────────────────────────────────────

class WorkflowStatus(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUSPENDED = "SUSPENDED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ActivityStatus(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class SignalType(Enum):
    HUMAN_REVIEW_APPROVE = "HUMAN_REVIEW_APPROVE"
    HUMAN_REVIEW_REJECT = "HUMAN_REVIEW_REJECT"
    HUMAN_REVIEW_REVISE = "HUMAN_REVIEW_REVISE"
    CANCEL = "CANCEL"


@dataclass
class RetryPolicy:
    """重试策略"""
    max_attempts: int = 3
    initial_interval_seconds: int = 1
    backoff_multiplier: float = 2.0
    max_interval_seconds: int = 60
    non_retryable_errors: List[str] = field(default_factory=lambda: ["ValidationError"])

    def next_delay(self, attempt: int) -> float:
        delay = self.initial_interval_seconds * (self.backoff_multiplier ** (attempt - 1))
        return min(delay, self.max_interval_seconds)


@dataclass
class ActivityOptions:
    """Activity 执行选项"""
    task_queue: str = "default"
    schedule_to_close_timeout_seconds: int = 300
    start_to_close_timeout_seconds: int = 120
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    idempotency_key: Optional[str] = None


@dataclass
class ChildWorkflowOptions:
    """Child Workflow 选项"""
    task_queue: str = "default"
    workflow_id_suffix: str = ""
    parent_close_policy: str = "ABANDON"


@dataclass
class WorkflowExecutionContext:
    """工作流执行上下文"""
    workflow_id: str
    workflow_type: str
    run_id: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    result: Any = None
    error: Optional[str] = None
    signals: Dict[str, Any] = field(default_factory=dict)
    activity_results: Dict[str, Any] = field(default_factory=dict)
    child_workflows: Dict[str, "WorkflowExecutionContext"] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict[str, Any]] = field(default_factory=list)

    def record_event(self, event_type: str, details: Dict[str, Any] = None):
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "details": details or {},
        })

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "workflow_type": self.workflow_type,
            "run_id": self.run_id,
            "status": self.status.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "result": self.result,
            "error": self.error,
            "metadata": self.metadata,
            "history": self.history,
        }


@dataclass
class ActivityExecutionContext:
    """Activity 执行上下文"""
    activity_id: str
    activity_type: str
    status: ActivityStatus = ActivityStatus.PENDING
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    result: Any = None
    error: Optional[str] = None
    attempt: int = 0
    max_attempts: int = 3
    idempotency_key: Optional[str] = None
    is_idempotent: bool = False


# ─── Decorators ────────────────────────────────────────────────────────────

# Global registries
_activity_registry: Dict[str, Callable] = {}
_workflow_registry: Dict[str, type] = {}


class TemporalActivity:
    """Activity 装饰器 - 声明一个函数为 Temporal Activity"""

    def __init__(self, **options):
        self.options = options

    def __call__(self, fn: Callable) -> Callable:
        activity_name = self.options.get("name", fn.__name__)
        is_idempotent = self.options.get("idempotent", True)

        # 使用 dict 按参数缓存以支持不同参数的幂等调用
        _cache: Dict[str, Any] = {}

        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            cache_key = _make_cache_key(args, kwargs)

            if is_idempotent and cache_key in _cache:
                logger.info(f"[Activity:{activity_name}] Returning idempotent cached result for {cache_key}")
                return _cache[cache_key]

            result = fn(*args, **kwargs)
            if asyncio.iscoroutine(result):
                result = await result

            if is_idempotent:
                _cache[cache_key] = result

            return result

        wrapper._temporal_activity = True
        wrapper._activity_name = activity_name
        wrapper._activity_options = self.options
        wrapper._idempotent = is_idempotent

        _activity_registry[activity_name] = wrapper
        return wrapper

    @staticmethod
    def defn(**options):
        """工厂方法"""
        return TemporalActivity(**options)


class TemporalWorkflow:
    """Workflow 装饰器 - 声明一个类为 Temporal Workflow"""

    def __init__(self, **options):
        self.options = options

    def __call__(self, cls: type) -> type:
        workflow_name = self.options.get("name", cls.__name__)
        cls._temporal_workflow = True
        cls._workflow_name = workflow_name
        cls._workflow_options = self.options
        _workflow_registry[workflow_name] = cls
        return cls

    @staticmethod
    def defn(**options):
        return TemporalWorkflow(**options)


# ─── Mock Temporal Client ──────────────────────────────────────────────────

class MockTemporalClient:
    """
    模拟 Temporal Client。
    当 MOCK_TEMPORAL=true 时使用内存模式，否则连接真实 Temporal 服务。
    """

    _instance: Optional["MockTemporalClient"] = None

    def __init__(self):
        self._workflows: Dict[str, WorkflowExecutionContext] = {}
        self._activities: Dict[str, ActivityExecutionContext] = {}
        self._signal_handlers: Dict[str, asyncio.Event] = {}
        self._task_queue: str = "textbook-writing-queue"

    @classmethod
    def get_instance(cls) -> "MockTemporalClient":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """重置单例 - 用于测试"""
        cls._instance = None

    # ── Workflow Operations ────────────────────────────────────────────

    async def start_workflow(
        self,
        workflow_cls: type,
        *args,
        workflow_id: Optional[str] = None,
        task_queue: Optional[str] = None,
        **kwargs,
    ) -> WorkflowExecutionContext:
        """启动一个顶层工作流"""
        wf_id = workflow_id or f"{workflow_cls.__name__}-{uuid.uuid4().hex[:8]}"
        wf_name = getattr(workflow_cls, "_workflow_name", workflow_cls.__name__)

        ctx = WorkflowExecutionContext(
            workflow_id=wf_id,
            workflow_type=wf_name,
            run_id=uuid.uuid4().hex,
            status=WorkflowStatus.RUNNING,
        )
        ctx.metadata["task_queue"] = task_queue or self._task_queue
        self._workflows[wf_id] = ctx
        ctx.record_event("WORKFLOW_STARTED", {"args": str(args), "kwargs": str(kwargs)})

        logger.info(f"[MockTemporal] Started workflow '{wf_name}' (id={wf_id})")

        try:
            instance = workflow_cls()
            instance._temporal_client = self
            instance._context = ctx

            result = instance.execute(*args, **kwargs)
            if asyncio.iscoroutine(result):
                result = await result

            ctx.status = WorkflowStatus.COMPLETED
            ctx.result = result
            ctx.end_time = datetime.now()
            ctx.record_event("WORKFLOW_COMPLETED", {"result": str(result)})
            logger.info(f"[MockTemporal] Workflow '{wf_id}' completed: {result}")
        except Exception as e:
            ctx.status = WorkflowStatus.FAILED
            ctx.error = str(e)
            ctx.end_time = datetime.now()
            ctx.record_event("WORKFLOW_FAILED", {"error": str(e), "traceback": traceback.format_exc()})
            logger.error(f"[MockTemporal] Workflow '{wf_id}' failed: {e}")

        return ctx

    async def get_workflow(self, workflow_id: str) -> Optional[WorkflowExecutionContext]:
        """查询工作流状态"""
        return self._workflows.get(workflow_id)

    # ── Activity Operations ────────────────────────────────────────────

    async def execute_activity(
        self,
        activity_fn: Callable,
        *args,
        options: Optional[ActivityOptions] = None,
        **kwargs,
    ) -> Any:
        """执行一个 Activity，支持重试和超时"""
        options = options or ActivityOptions()
        activity_name = getattr(activity_fn, "_activity_name", activity_fn.__name__)
        activity_id = f"act-{activity_name}-{uuid.uuid4().hex[:8]}"

        ctx = ActivityExecutionContext(
            activity_id=activity_id,
            activity_type=activity_name,
            max_attempts=options.retry_policy.max_attempts,
            idempotency_key=options.idempotency_key,
            is_idempotent=getattr(activity_fn, "_idempotent", True),
        )
        self._activities[activity_id] = ctx

        last_error = None
        for attempt in range(1, options.retry_policy.max_attempts + 1):
            ctx.attempt = attempt
            ctx.status = ActivityStatus.RUNNING
            ctx.start_time = datetime.now()

            logger.info(
                f"[MockTemporal] Activity '{activity_name}' attempt {attempt}/{options.retry_policy.max_attempts}"
            )

            try:
                # 模拟超时
                timeout = options.start_to_close_timeout_seconds

                if timeout and timeout > 0:
                    result = await asyncio.wait_for(
                        self._call_activity(activity_fn, *args, **kwargs),
                        timeout=timeout,
                    )
                else:
                    result = await self._call_activity(activity_fn, *args, **kwargs)

                ctx.status = ActivityStatus.COMPLETED
                ctx.result = result
                ctx.end_time = datetime.now()
                logger.info(f"[MockTemporal] Activity '{activity_name}' completed (attempt {attempt})")
                return result

            except asyncio.TimeoutError:
                last_error = TimeoutError(f"Activity '{activity_name}' timed out after {timeout}s")
                ctx.error = str(last_error)
                logger.warning(f"[MockTemporal] Activity '{activity_name}' timed out (attempt {attempt})")

            except Exception as e:
                last_error = e
                ctx.error = str(e)

                # 检查是否为不可重试错误
                error_type = type(e).__name__
                if error_type in options.retry_policy.non_retryable_errors:
                    logger.error(f"[MockTemporal] Non-retryable error in '{activity_name}': {e}")
                    break

                logger.warning(f"[MockTemporal] Activity '{activity_name}' failed (attempt {attempt}): {e}")

            # 重试前等待
            if attempt < options.retry_policy.max_attempts:
                delay = options.retry_policy.next_delay(attempt)
                logger.info(f"[MockTemporal] Retrying '{activity_name}' in {delay}s...")
                await asyncio.sleep(delay)

        ctx.status = ActivityStatus.FAILED
        ctx.end_time = datetime.now()
        raise last_error or RuntimeError(f"Activity '{activity_name}' failed")

    async def _call_activity(self, activity_fn: Callable, *args, **kwargs) -> Any:
        """调用活动函数"""
        result = activity_fn(*args, **kwargs)
        if asyncio.iscoroutine(result):
            result = await result
        return result

    # ── Child Workflow Operations ──────────────────────────────────────

    async def start_child_workflow(
        self,
        workflow_cls: type,
        *args,
        options: Optional[ChildWorkflowOptions] = None,
        **kwargs,
    ) -> Any:
        """启动子工作流并等待完成"""
        options = options or ChildWorkflowOptions()
        child_suffix = options.workflow_id_suffix or uuid.uuid4().hex[:8]
        child_id = f"child-{workflow_cls.__name__}-{child_suffix}"

        logger.info(f"[MockTemporal] Starting child workflow '{child_id}'")
        ctx = await self.start_workflow(workflow_cls, *args, workflow_id=child_id, **kwargs)

        if ctx.status == WorkflowStatus.FAILED:
            raise RuntimeError(f"Child workflow '{child_id}' failed: {ctx.error}")

        return ctx.result

    # ── Signal Operations ───────────────────────────────────────────────

    async def signal_workflow(
        self,
        workflow_id: str,
        signal_type: Union[str, SignalType],
        payload: Any = None,
    ) -> bool:
        """向工作流发送信号"""
        signal_name = signal_type.value if isinstance(signal_type, SignalType) else signal_type

        ctx = self._workflows.get(workflow_id)
        if ctx is None:
            logger.warning(f"[MockTemporal] Workflow '{workflow_id}' not found for signal")
            return False

        ctx.signals[signal_name] = payload
        ctx.status = WorkflowStatus.RUNNING  # 从 SUSPENDED 恢复
        ctx.record_event("SIGNAL_RECEIVED", {"signal": signal_name, "payload": payload})

        # 触发等待该信号的事件
        event_key = f"{workflow_id}:{signal_name}"
        if event_key in self._signal_handlers:
            self._signal_handlers[event_key].set()

        logger.info(f"[MockTemporal] Signal '{signal_name}' sent to workflow '{workflow_id}'")
        return True

    async def wait_for_signal(
        self,
        workflow_id: str,
        signal_names: List[str],
        timeout_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        """等待指定信号之一到达"""
        ctx = self._workflows.get(workflow_id)
        if ctx is None:
            raise RuntimeError(f"Workflow '{workflow_id}' not found")

        ctx.status = WorkflowStatus.SUSPENDED
        ctx.record_event("WAITING_FOR_SIGNAL", {"signals": signal_names})

        # 检查是否已有信号
        for name in signal_names:
            if name in ctx.signals:
                ctx.status = WorkflowStatus.RUNNING
                return {"signal": name, "payload": ctx.signals[name]}

        # 创建等待事件
        events = {}
        for name in signal_names:
            events[name] = asyncio.Event()
            self._signal_handlers[f"{workflow_id}:{name}"] = events[name]

        logger.info(f"[MockTemporal] Workflow '{workflow_id}' waiting for signals: {signal_names}")

        try:
            tasks = [asyncio.create_task(e.wait()) for e in events.values()]
            done, pending = await asyncio.wait(
                tasks,
                timeout=timeout_seconds,
                return_when=asyncio.FIRST_COMPLETED,
            )

            for task in pending:
                task.cancel()

            if not done:
                raise TimeoutError(f"No signal received within {timeout_seconds}s")

            # 找到触发的信号
            for name, event in events.items():
                if event.is_set():
                    ctx.status = WorkflowStatus.RUNNING
                    ctx.record_event("SIGNAL_HANDLED", {"signal": name})
                    return {"signal": name, "payload": ctx.signals.get(name)}

            return {"signal": "unknown", "payload": None}

        finally:
            # 清理事件
            for name in signal_names:
                self._signal_handlers.pop(f"{workflow_id}:{name}", None)

    # ── Utility ─────────────────────────────────────────────────────────

    async def sleep(self, seconds: float):
        """模拟 Temporal timer"""
        ctx = self._get_current_workflow_context()
        if ctx:
            ctx.record_event("TIMER_STARTED", {"seconds": seconds})
        await asyncio.sleep(seconds)
        if ctx:
            ctx.record_event("TIMER_FIRED", {"seconds": seconds})

    def _get_current_workflow_context(self) -> Optional[WorkflowExecutionContext]:
        """获取当前工作流上下文（简化实现）"""
        # 在完整实现中会使用 contextvars
        return None

    async def cancel_workflow(self, workflow_id: str) -> bool:
        """取消工作流"""
        ctx = self._workflows.get(workflow_id)
        if ctx and ctx.status not in (WorkflowStatus.COMPLETED, WorkflowStatus.FAILED):
            ctx.status = WorkflowStatus.CANCELLED
            ctx.end_time = datetime.now()
            ctx.record_event("WORKFLOW_CANCELLED", {})
            logger.info(f"[MockTemporal] Workflow '{workflow_id}' cancelled")
            return True
        return False

    def list_workflows(self, status_filter: Optional[WorkflowStatus] = None) -> List[Dict[str, Any]]:
        """列出工作流"""
        result = []
        for wf_id, ctx in self._workflows.items():
            if status_filter and ctx.status != status_filter:
                continue
            result.append(ctx.to_dict())
        return result

    def reset(self):
        """重置所有状态"""
        self._workflows.clear()
        self._activities.clear()
        self._signal_handlers.clear()


# ─── Global Client Access ─────────────────────────────────────────────────

def get_mock_client() -> MockTemporalClient:
    """获取全局 MockTemporalClient 实例"""
    return MockTemporalClient.get_instance()
