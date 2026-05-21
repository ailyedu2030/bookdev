"""
F00: 事件总线工厂

根据配置创建对应的事件总线实例。
无Kafka时自动使用Mock总线。
"""

import asyncio
import logging
import json
import os
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def create_event_bus(config: Optional[dict] = None):
    """
    创建事件总线实例

    Args:
        config: 可选配置字典
            use_mock: 是否使用Mock总线 (默认: True)
            bootstrap_servers: Kafka服务器地址 (默认: localhost:9092)
            consumer_group: 消费者组名 (默认: textbook-system)

    Returns:
        MockEventBus 或 RealEventBus 实例
    """
    if config is None:
        config = {}

    use_mock = config.get("use_mock", True)

    if use_mock:
        from f00_kafka_eventbus.mock_bus import MockEventBus
        return MockEventBus()
    else:
        return RealEventBus(config=config)


class RealEventBus:
    """
    Real Kafka Event Bus

    基于RealKafkaProducer和RealKafkaConsumer的实现。
    支持发布/订阅、事件溯源和死信队列。
    """

    # Local fallback log path for DLQ failures
    DLQ_FALLBACK_DIR = "/var/log/bookdop/dlq_fallback"

    def __init__(self, config: Optional[dict] = None):
        if config is None:
            config = {}

        self._bootstrap_servers = config.get("bootstrap_servers", "localhost:9092")
        self._consumer_group = config.get("consumer_group", "textbook-system")
        self._topic_prefix = config.get("topic_prefix", "textbook")

        self._producer: Optional["RealKafkaProducer"] = None
        self._consumers: dict = {}
        self._subscribers: dict = {}
        self._dlq_handlers: list = []
        self._running = False
        self._dlq_handler: Optional["DLQHandler"] = None

    async def initialize(self) -> None:
        """初始化事件总线"""
        from f00_kafka_eventbus.real_producer import RealKafkaProducer
        from f00_kafka_eventbus.topic_manager import KafkaTopicManager
        from f00_kafka_eventbus.dlq_handler import DLQHandler

        self._producer = RealKafkaProducer(
            bootstrap_servers=self._bootstrap_servers,
        )
        await self._producer.start()

        self._dlq_handler = DLQHandler(
            producer=self._producer,
            dlq_topic=f"{self._topic_prefix}.dlq",
        )

        topic_manager = KafkaTopicManager(
            bootstrap_servers=self._bootstrap_servers,
        )
        topics = [
            {"name": f"{self._topic_prefix}.{name}", **cfg}
            for name, cfg in KafkaTopicManager.TOPICS.items()
        ]
        await topic_manager.create_topics(topics)

    async def shutdown(self) -> None:
        """关闭事件总线"""
        self._running = False

        for consumer in self._consumers.values():
            await consumer.stop()

        if self._producer:
            await self._producer.stop()

    def subscribe(
        self,
        event_type: str,
        handler,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> int:
        """
        订阅事件

        INF-006: Added validation to ensure handler is callable.

        Args:
            event_type: 事件类型
            handler: 事件处理函数
            max_retries: 失败最大重试次数
            retry_delay: 重试间隔(秒)

        Returns:
            subscription_id: 订阅ID

        Raises:
            TypeError: If handler is not callable
            ValueError: If event_type is empty
        """
        # INF-006: Validate handler is callable
        if not callable(handler):
            raise TypeError(f"handler must be a callable object, got {type(handler).__name__}")

        # INF-006: Validate event_type is not empty
        if not event_type or not event_type.strip():
            raise ValueError("event_type cannot be empty")

        from f00_kafka_eventbus.real_consumer import RealKafkaConsumer

        topic = f"{self._topic_prefix}.{event_type}"

        if topic not in self._subscribers:
            self._subscribers[topic] = []

        sub_id = len(self._subscribers[topic])
        self._subscribers[topic].append({
            "id": sub_id,
            "event_type": event_type,
            "handler": handler,
            "max_retries": max_retries,
            "retry_delay": retry_delay,
        })

        return sub_id

    def subscribe_dead_letter(self, handler) -> None:
        """订阅死信队列"""
        if self._dlq_handler:
            self._dlq_handler.subscribe(handler)

    async def publish(self, event) -> None:
        """
        发布事件

        Args:
            event: Event对象
        """
        if self._producer is None:
            raise RuntimeError("EventBus not initialized. Call initialize() first.")

        topic_prefixed = f"{self._topic_prefix}.{event.event_type}"

        await self._producer.send(
            topic=topic_prefixed,
            value={
                "event_id": event.event_id,
                "event_type": event.event_type,
                "timestamp": event.timestamp.isoformat(),
                "payload": event.payload,
            },
            key=event.event_id,
        )

    async def _execute_handler_with_retry(
        self,
        handler,
        msg: dict,
        max_retries: int,
        retry_delay: float,
    ) -> bool:
        """
        Execute handler with retry logic and exponential backoff.

        Args:
            handler: Event handler function
            msg: Message to process
            max_retries: Maximum number of retry attempts
            retry_delay: Base delay between retries (seconds)

        Returns:
            True if handler succeeded, False otherwise
        """
        last_error = None
        exponential_base = 2.0
        max_delay = 60.0

        for attempt in range(max_retries + 1):
            try:
                await handler(msg)
                if attempt > 0:
                    logger.info(
                        f"Retry {attempt} succeeded for handler {handler.__name__}"
                    )
                return True
            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    # Calculate delay with exponential backoff and jitter
                    import random
                    delay = min(retry_delay * (exponential_base ** attempt), max_delay)
                    delay = delay * (0.5 + random.random() * 0.5)  # Add jitter
                    logger.warning(
                        f"Handler {handler.__name__} attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"Handler {handler.__name__} failed after {max_retries + 1} attempts: {e}"
                    )

        # All retries exhausted, return False
        return False

    def _log_to_fallback_file(self, msg: dict, error: Exception, handler_name: str) -> None:
        """
        Log failed message to local fallback file when DLQ fails.

        Args:
            msg: The failed message
            error: The exception that caused the failure
            handler_name: Name of the handler that failed
        """
        import traceback as tb

        try:
            # Ensure directory exists
            os.makedirs(self.DLQ_FALLBACK_DIR, exist_ok=True)

            fallback_file = os.path.join(
                self.DLQ_FALLBACK_DIR,
                f"dlq_fallback_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json"
            )

            fallback_entry = {
                "event": msg,
                "error": {
                    "type": type(error).__name__,
                    "message": str(error),
                },
                "handler_name": handler_name,
                "timestamp": datetime.utcnow().isoformat(),
                "traceback": tb.format_exc(),
            }

            with open(fallback_file, 'w') as f:
                json.dump(fallback_entry, f, indent=2, default=str)

            logger.info(f"Message logged to fallback file: {fallback_file}")
        except Exception as fallback_error:
            logger.error(
                f"Failed to write fallback log: {fallback_error}. "
                f"Original error: {error}"
            )

    async def start_consuming(self) -> None:
        """开始消费消息"""
        from f00_kafka_eventbus.real_consumer import RealKafkaConsumer

        self._running = True

        for topic, subs in self._subscribers.items():
            consumer = RealKafkaConsumer(
                bootstrap_servers=self._bootstrap_servers,
                group_id=self._consumer_group,
                topics=[topic],
                enable_auto_commit=False,  # KAFKA-006: Manual commit for reliability
            )
            await consumer.start()

            async def create_handler(sub_list):
                async def handler(msg):
                    """
                    Process message with proper retry logic and DLQ handling.
                    Ensures consumer continues even after handler failures.
                    """
                    # KAFKA-015: Implement deduplication based on event_id
                    event_id = msg.get("event_id")
                    if event_id and hasattr(self, '_processed_events'):
                        if event_id in self._processed_events:
                            logger.debug(f"Duplicate event detected: {event_id}, skipping")
                            return
                        self._processed_events.add(event_id)
                        # Keep set bounded to avoid memory leak
                        if len(self._processed_events) > 100000:
                            self._processed_events = set(list(self._processed_events)[-50000:])

                    for sub in sub_list:
                        try:
                            # KAFKA-005: Implement actual retry logic with exponential backoff
                            success = await self._execute_handler_with_retry(
                                handler=sub["handler"],
                                msg=msg,
                                max_retries=sub["max_retries"],
                                retry_delay=sub["retry_delay"],
                            )

                            if not success:
                                # All retries exhausted, send to DLQ
                                if self._dlq_handler:
                                    try:
                                        await self._dlq_handler.send_to_dlq(
                                            msg,
                                            Exception("Handler failed after max retries"),
                                            sub["handler"].__name__,
                                        )
                                    except Exception as dlq_error:
                                        # KAFKA-014: DLQ failure should not cause message loss
                                        logger.error(
                                            f"Failed to send to DLQ: {dlq_error}. "
                                            f"Logging to fallback file instead."
                                        )
                                        self._log_to_fallback_file(
                                            msg,
                                            dlq_error,
                                            sub["handler"].__name__,
                                        )
                        except Exception as e:
                            # KAFKA-012: Ensure we continue to next message even on unexpected errors
                            logger.error(
                                f"Unexpected error in handler loop: {e}",
                                exc_info=True
                            )
                            continue

                return handler

            self._consumers[topic] = consumer
            # Initialize deduplication set for this consumer
            if not hasattr(self, '_processed_events'):
                self._processed_events = set()
            await consumer.consume_in_background(await create_handler(subs))

    async def stop_consuming(self) -> None:
        """停止消费消息"""
        self._running = False
        for consumer in self._consumers.values():
            await consumer.stop()
        self._consumers.clear()
