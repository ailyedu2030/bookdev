"""
F00: Mock事件总线

无需Kafka服务器即可运行的内存事件总线。
支持发布/订阅、事件溯源、死信队列和至少一次语义。
"""

import threading
import fnmatch
import uuid
import time
import traceback
from collections import deque
from typing import Callable, Optional, Any


class MockEventBus:
    """
    Mock事件总线

    特性:
    - 内存中发布/订阅
    - 通配符模式匹配 (e.g., "chapter.*")
    - 事件溯源 (不可变追加日志)
    - 死信队列 (DLQ)
    - 至少一次语义 (重试)
    - 线程安全
    """

    def __init__(self):
        self._subscribers: dict[str, list[dict]] = {}  # event_type -> [subscription]
        self._dlq_handlers: list[Callable] = []
        self._event_log: list[Any] = []
        self._lock = threading.RLock()
        self._shutdown = False
        self._sub_id_counter = 0

    def subscribe(
        self,
        event_type: str,
        handler: Callable,
        max_retries: int = 0,
        retry_delay: float = 0.1,
    ) -> int:
        """
        订阅事件

        Args:
            event_type: 事件类型 (支持 * 通配符)
            handler: 事件处理函数
            max_retries: 失败最大重试次数 (0=不重试)
            retry_delay: 重试间隔(秒)

        Returns:
            subscription_id: 订阅ID，用于取消订阅
        """
        with self._lock:
            if self._shutdown:
                raise RuntimeError("EventBus已关闭，无法订阅")

            self._sub_id_counter += 1
            sub_id = self._sub_id_counter

            subscription = {
                "id": sub_id,
                "event_type": event_type,
                "handler": handler,
                "max_retries": max_retries,
                "retry_delay": retry_delay,
            }

            if event_type not in self._subscribers:
                self._subscribers[event_type] = []

            self._subscribers[event_type].append(subscription)
            return sub_id

    def unsubscribe(self, subscription_id: int):
        """取消订阅"""
        with self._lock:
            for event_type, subs in list(self._subscribers.items()):
                self._subscribers[event_type] = [
                    s for s in subs if s["id"] != subscription_id
                ]
                if not self._subscribers[event_type]:
                    del self._subscribers[event_type]

    def subscribe_dead_letter(self, handler: Callable):
        """订阅死信队列"""
        with self._lock:
            self._dlq_handlers.append(handler)

    def publish(self, event: Any):
        """
        发布事件

        事件被追加到不可变日志，然后分发给匹配的订阅者。
        """
        if self._shutdown:
            return

        with self._lock:
            self._event_log.append(event)

            # 收集匹配的订阅者
            matched_subs = []
            for pattern, subs in self._subscribers.items():
                if fnmatch.fnmatch(event.event_type, pattern):
                    matched_subs.extend(subs)

        # 在锁外分发事件（避免死锁）
        for sub in matched_subs:
            self._deliver_event(sub, event)

    def _deliver_event(self, subscription: dict, event: Any):
        """投递事件到单个订阅者，支持重试"""
        handler = subscription["handler"]
        max_retries = subscription["max_retries"]
        retry_delay = subscription["retry_delay"]

        attempts = 0
        last_error = None

        while attempts <= max_retries:
            try:
                handler(event)
                return  # 成功
            except Exception as e:
                last_error = e
                attempts += 1
                if attempts <= max_retries:
                    time.sleep(retry_delay)

        # 所有重试失败 -> 死信队列
        self._send_to_dlq(event, last_error)

    def _send_to_dlq(self, original_event: Any, error: Exception):
        """将失败事件发送到死信队列"""
        from f00_kafka_eventbus.event_definitions import Event
        from datetime import datetime

        dlq_event = Event(
            event_type="pipeline.stage_changed",
            timestamp=datetime.utcnow(),
            payload={
                "original_event_type": original_event.event_type,
                "original_event_id": original_event.event_id,
                "original_payload": original_event.payload,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "traceback": traceback.format_exc(),
            },
        )

        with self._lock:
            for handler in self._dlq_handlers:
                try:
                    handler(dlq_event)
                except Exception:
                    pass  # DLQ处理器失败不传播

    def get_event_log(self) -> tuple:
        """获取不可变事件日志 (只读)"""
        with self._lock:
            return tuple(self._event_log)

    def replay_log(self, handler: Callable):
        """重放事件日志"""
        with self._lock:
            events = list(self._event_log)

        for event in events:
            try:
                handler(event)
            except Exception:
                pass  # 重放时处理器异常不中断

    def shutdown(self):
        """关闭事件总线"""
        with self._lock:
            self._shutdown = True
