"""
Mock Temporal Client - 模拟 Temporal SDK 行为，支持 MOCK_TEMPORAL 环境变量切换。

支持:
- Workflow 注册和执行
- Activity 注册和执行 (带重试/超时/幂等)
- Child Workflow
- Signal (Human-in-the-loop)
- Timer/Sleep
- Heartbeat (long-running activity)
"""

import asyncio
import functools
import hashlib
import logging
import os
import traceback
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional, TypeVar

logger = logging.getLogger(__name__)

MOCK_TEMPORAL = os.environ.get("MOCK_TEMPORAL", "true").lower() in ("1", "true", "yes")

T = TypeVar("T")


def _make_cache_key(args: tuple, kwargs: dict) -> str:
    """生成幂等缓存键"""
    parts = [str(a) for a in args]
    parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    return hashlib.sha256("|".join(parts).encode()).hexdigest()


# ─── Global Idempotency Cache (External Storage) ─────────────────────────────
# FIX TEMP-012: 使用全局外部存储而不是闭包中的局部变量
_idempotency_cache: dict[str, Any] = {}
_idempotency_lock = asyncio.Lock()


async def get_cached_result(cache_key: str) -> Any | None:
    """从全局缓存获取幂等结果"""
    return _idempotency_cache.get(cache_key)


async def store_cached_result(cache_key: str, result: Any) -> None:
    """存储幂等结果到全局缓存"""
    async with _idempotency_lock:
        _idempotency_cache[cache_key] = result


def clear_idempotency_cache() -> None:
    """清空幂等缓存 (用于测试)"""
    global _idempotency_cache
    _idempotency_cache = {}


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
    non_retryable_errors: list[str] = field(default_factory=lambda: ["ValidationError"])

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
    idempotency_key: str | None = None
    heartbeat_timeout_seconds: int = 30  # TEMP-016: 心跳超时


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
    end_time: datetime | None = None
    result: Any = None
    error: str | None = None
    signals: dict[str, Any] = field(default_factory=dict)
    activity_results: dict[str, Any] = field(default_factory=dict)
    child_workflows: dict[str, "WorkflowExecutionContext"] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)
    # TEMP-019: 持久化状态存储
    workflow_state: dict[str, Any] = field(default_factory=dict)

    def record_event(self, event_type: str, details: dict[str, Any] = None):
        self.history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "details": details or {},
            }
        )

    def to_dict(self) -> dict[str, Any]:
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
            "workflow_state": self.workflow_state,  # TEMP-019
        }


@dataclass
class ActivityExecutionContext:
    """Activity 执行上下文"""

    activity_id: str
    activity_type: str
    status: ActivityStatus = ActivityStatus.PENDING
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None
    result: Any = None
    error: str | None = None
    attempt: int = 0
    max_attempts: int = 3
    idempotency_key: str | None = None
    is_idempotent: bool = False
    last_heartbeat: datetime = field(default_factory=datetime.now)
    heartbeat_count: int = 0


# ─── Workflow State Persistence ───────────────────────────────────────────────
# TEMP-019: 全局状态存储，模拟 Temporal 的状态持久化
_workflow_state_store: dict[str, dict[str, Any]] = {}


def save_workflow_state(workflow_id: str, state: dict[str, Any]) -> None:
    """保存工作流状态到持久化存储"""
    _workflow_state_store[workflow_id] = state


def load_workflow_state(workflow_id: str) -> dict[str, Any]:
    """加载工作流状态"""
    return _workflow_state_store.get(workflow_id, {})


def clear_workflow_state(workflow_id: str) -> None:
    """清除工作流状态"""
    if workflow_id in _workflow_state_store:
        del _workflow_state_store[workflow_id]


# ─── Decorators ────────────────────────────────────────────────────────────

# Global registries
_activity_registry: dict[str, Callable] = {}
_workflow_registry: dict[str, type] = {}


class TemporalActivity:
    """Activity 装饰器 - 声明一个函数为 Temporal Activity"""

    def __init__(self, **options):
        self.options = options

    def __call__(self, fn: Callable) -> Callable:
        activity_name = self.options.get("name", fn.__name__)
        is_idempotent = self.options.get("idempotent", True)

        # TEMP-012 FIX: 不再使用闭包中的局部变量_cache
        # 幂等性现在通过全局_idempotency_cache和idempotency_key共同实现

        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            # 生成缓存键 (基于参数，不是尝试次数)
            cache_key = _make_cache_key(args, kwargs)

            # TEMP-013 FIX: 如果有显式的idempotency_key，使用它而不是生成键
            # 这允许调用者基于内容哈希来设置幂等键
            options = kwargs.get("options")
            if options and hasattr(options, "idempotency_key") and options.idempotency_key:
                cache_key = options.idempotency_key

            # TEMP-012 FIX: 使用全局外部存储
            if is_idempotent:
                cached = await get_cached_result(cache_key)
                if cached is not None:
                    logger.info(
                        f"[Activity:{activity_name}] Returning idempotent cached result for {cache_key[:16]}..."
                    )
                    return cached

            result = fn(*args, **kwargs)
            if asyncio.iscoroutine(result):
                result = await result

            if is_idempotent:
                await store_cached_result(cache_key, result)

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


class TemporalQuery:
    """Query 装饰器 - 为工作流添加查询处理器"""

    def __init__(self, **options):
        self.options = options

    def __call__(self, fn: Callable) -> Callable:
        query_name = self.options.get("name", fn.__name__)
        fn._temporal_query = True
        fn._query_name = query_name
        fn._query_options = self.options
        return fn

    @staticmethod
    def defn(**options):
        return TemporalQuery(**options)


# ─── Mock Temporal Client ──────────────────────────────────────────────────


class MockTemporalClient:
    """
    模拟 Temporal Client。
    当 MOCK_TEMPORAL=true 时使用内存模式，否则连接真实 Temporal 服务。
    """

    _instance: Optional["MockTemporalClient"] = None

    def __init__(self):
        self._workflows: dict[str, WorkflowExecutionContext] = {}
        self._activities: dict[str, ActivityExecutionContext] = {}
        self._signal_handlers: dict[str, asyncio.Event] = {}
        self._task_queue: str = "textbook-writing-queue"
        # TEMP-023: 配置常量
        self._config = {
            "outline_review_timeout_seconds": int(os.environ.get("OUTLINE_REVIEW_TIMEOUT", "86400")),
            "final_review_timeout_seconds": int(os.environ.get("FINAL_REVIEW_TIMEOUT", "86400")),
            "heartbeat_interval_seconds": 30,
        }

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
        workflow_id: str | None = None,
        task_queue: str | None = None,
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

            # TEMP-019: 从持久化存储恢复工作流状态
            saved_state = load_workflow_state(wf_id)
            if saved_state:
                instance._state = saved_state.get("_workflow_state", {})
                ctx.workflow_state = saved_state
                logger.info(f"[MockTemporal] Restored workflow state for '{wf_id}'")

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

    async def get_workflow(self, workflow_id: str) -> WorkflowExecutionContext | None:
        """查询工作流状态"""
        return self._workflows.get(workflow_id)

    # TEMP-016: 心跳机制
    async def send_heartbeat(self, activity_id: str, details: dict[str, Any] = None) -> None:
        """发送活动心跳"""
        if activity_id in self._activities:
            ctx = self._activities[activity_id]
            ctx.last_heartbeat = datetime.now()
            ctx.heartbeat_count += 1
            ctx.record_event("HEARTBEAT", details or {})
            logger.debug(f"[MockTemporal] Heartbeat for activity '{activity_id}': count={ctx.heartbeat_count}")

    async def check_heartbeat(self, activity_id: str) -> bool:
        """检查活动是否还活着"""
        if activity_id not in self._activities:
            return False
        ctx = self._activities[activity_id]
        elapsed = (datetime.now() - ctx.last_heartbeat).total_seconds()
        return elapsed < self._config["heartbeat_interval_seconds"] * 2

    # ── Activity Operations ────────────────────────────────────────────

    async def execute_activity(
        self,
        activity_fn: Callable,
        *args,
        options: ActivityOptions | None = None,
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

        # TEMP-016: 心跳任务
        heartbeat_task = None
        if options.heartbeat_timeout_seconds > 0:

            async def heartbeat_loop():
                while ctx.status == ActivityStatus.RUNNING:
                    await asyncio.sleep(options.heartbeat_timeout_seconds)
                    await self.send_heartbeat(activity_id, {"activity": activity_name})

            heartbeat_task = asyncio.create_task(heartbeat_loop())

        last_error = None
        try:
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
        finally:
            if heartbeat_task:
                heartbeat_task.cancel()
                try:
                    await heartbeat_task
                except asyncio.CancelledError:
                    pass

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
        options: ChildWorkflowOptions | None = None,
        **kwargs,
    ) -> Any:
        """启动子工作流并等待完成"""
        options = options or ChildWorkflowOptions()
        child_suffix = options.workflow_id_suffix or uuid.uuid4().hex[:8]
        child_id = f"child-{workflow_cls.__name__}-{child_suffix}"

        logger.info(f"[MockTemporal] Starting child workflow '{child_id}'")
        ctx = await self.start_workflow(workflow_cls, *args, workflow_id=child_id, **kwargs)

        # TEMP-008: 子工作流失败时的补偿逻辑
        if ctx.status == WorkflowStatus.FAILED:
            # 记录失败以便后续补偿
            logger.error(f"[MockTemporal] Child workflow '{child_id}' failed: {ctx.error}")
            # 补偿逻辑：在编排器中清理已部分完成的工作
            raise ChildWorkflowFailedError(f"Child workflow '{child_id}' failed: {ctx.error}", child_id, ctx.error)

        return ctx.result

    # ── Signal Operations ────────────────────────────────────────────────

    async def signal_workflow(
        self,
        workflow_id: str,
        signal_type: str | SignalType,
        payload: Any = None,
    ) -> bool:
        """向工作流发送信号"""
        signal_name = signal_type.value if isinstance(signal_type, SignalType) else signal_type

        ctx = self._workflows.get(workflow_id)
        if ctx is None:
            logger.warning(f"[MockTemporal] Workflow '{workflow_id}' not found for signal")
            return False

        # TEMP-024: 信号验证
        if not signal_name or signal_name not in [s.value for s in SignalType] + list(SignalType.__members__.values()):
            logger.warning(f"[MockTemporal] Invalid signal type: {signal_name}")
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
        signal_names: list[str],
        timeout_seconds: int | None = None,
    ) -> dict[str, Any]:
        """等待指定信号之一到达"""
        ctx = self._workflows.get(workflow_id)
        if ctx is None:
            raise RuntimeError(f"Workflow '{workflow_id}' not found")

        # TEMP-023: 从配置读取超时时间
        if timeout_seconds is None:
            # 根据等待的信号类型决定默认超时
            if "OUTLINE_REVIEW" in signal_names[0] if signal_names else False:
                timeout_seconds = self._config["outline_review_timeout_seconds"]
            else:
                timeout_seconds = self._config["final_review_timeout_seconds"]

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
                # TEMP-009: 超时时的恢复机制
                logger.warning(f"[MockTemporal] Signal wait timed out for workflow '{workflow_id}'")
                ctx.record_event("SIGNAL_TIMEOUT", {"signals": signal_names, "timeout": timeout_seconds})
                # 返回超时信号，让调用者决定如何处理
                return {
                    "signal": "TIMEOUT",
                    "payload": {
                        "timeout_seconds": timeout_seconds,
                        "signals_expected": signal_names,
                        "message": f"No signal received within {timeout_seconds}s",
                    },
                }

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

    # ── State Persistence Operations (TEMP-019) ──────────────────────────

    async def save_state(self, workflow_id: str, state: dict[str, Any]) -> None:
        """保存工作流状态 (模拟 Temporal 的状态持久化)"""
        ctx = self._workflows.get(workflow_id)
        if ctx:
            ctx.workflow_state = state
        save_workflow_state(workflow_id, {"_workflow_state": state, "saved_at": datetime.now().isoformat()})

    async def load_state(self, workflow_id: str) -> dict[str, Any]:
        """加载工作流状态"""
        return load_workflow_state(workflow_id)

    # ── Query Operations (TEMP-022) ─────────────────────────────────────

    async def query_workflow(
        self,
        workflow_id: str,
        query_type: str,
        args: tuple = (),
        kwargs: dict[str, Any] = None,
    ) -> Any:
        """查询工作流状态"""
        ctx = self._workflows.get(workflow_id)
        if ctx is None:
            raise RuntimeError(f"Workflow '{workflow_id}' not found")

        # 查找注册的 query handler
        wf_type = ctx.workflow_type
        wf_cls = _workflow_registry.get(wf_type)
        if not wf_cls:
            raise RuntimeError(f"Unknown workflow type: {wf_type}")

        # 获取类的 query 方法
        query_method = getattr(wf_cls, query_type, None)
        if not query_method or not getattr(query_method, "_temporal_query", False):
            raise RuntimeError(f"Query '{query_type}' not found on workflow '{wf_type}'")

        # 创建临时实例来执行 query
        instance = wf_cls()
        instance._temporal_client = self
        instance._context = ctx
        # 恢复状态
        instance._state = ctx.workflow_state

        kwargs = kwargs or {}
        result = query_method(instance, *args, **kwargs)
        if asyncio.iscoroutine(result):
            result = await result
        return result

    # ── Utility ─────────────────────────────────────────────────────────

    async def sleep(self, seconds: float):
        """模拟 Temporal timer"""
        ctx = self._get_current_workflow_context()
        if ctx:
            ctx.record_event("TIMER_STARTED", {"seconds": seconds})
        await asyncio.sleep(seconds)
        if ctx:
            ctx.record_event("TIMER_FIRED", {"seconds": seconds})

    def _get_current_workflow_context(self) -> WorkflowExecutionContext | None:
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

    def list_workflows(self, status_filter: WorkflowStatus | None = None) -> list[dict[str, Any]]:
        """列出工作流"""
        result = []
        for _wf_id, ctx in self._workflows.items():
            if status_filter and ctx.status != status_filter:
                continue
            result.append(ctx.to_dict())
        return result

    def reset(self):
        """重置所有状态"""
        self._workflows.clear()
        self._activities.clear()
        self._signal_handlers.clear()
        clear_idempotency_cache()
        _workflow_state_store.clear()


class ChildWorkflowFailedError(Exception):
    """子工作流失败异常 (TEMP-008)"""

    def __init__(self, message: str, child_id: str, original_error: str):
        super().__init__(message)
        self.child_id = child_id
        self.original_error = original_error


# ─── Global Client Access ─────────────────────────────────────────────────


def get_mock_client() -> MockTemporalClient:
    """获取全局 MockTemporalClient 实例"""
    return MockTemporalClient.get_instance()
