"""
Real Kafka Consumer using aiokafka
"""

from aiokafka import AIOKafkaConsumer
from typing import Callable, Optional, Dict, Any, List
import asyncio
import json
import logging

logger = logging.getLogger(__name__)


class RealKafkaConsumer:
    """
    Real Kafka Consumer using aiokafka

    Features:
    - Async message consumption
    - Consumer group support
    - Automatic deserialization
    - Configurable offset reset
    """

    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        group_id: str = "textbook-consumer",
        auto_offset_reset: str = "earliest",
        topics: Optional[List[str]] = None,
    ):
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.auto_offset_reset = auto_offset_reset
        self.topics = topics or []
        self._consumer: Optional[AIOKafkaConsumer] = None
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the consumer and connect to Kafka"""
        if self._consumer is not None:
            logger.warning("Consumer already started")
            return

        self._consumer = AIOKafkaConsumer(
            *self.topics,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            auto_offset_reset=self.auto_offset_reset,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            key_deserializer=lambda k: k.decode("utf-8") if k else None,
            enable_auto_commit=True,
            auto_commit_interval_ms=5000,
        )
        await self._consumer.start()
        self._running = True
        logger.info(
            f"Kafka consumer started, connected to {self.bootstrap_servers}, "
            f"group={self.group_id}, topics={self.topics}"
        )

    async def stop(self) -> None:
        """Stop the consumer"""
        self._running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        if self._consumer:
            await self._consumer.stop()
            self._consumer = None
            logger.info("Kafka consumer stopped")

    async def consume(self, handler: Callable[[Dict[str, Any]], None]) -> None:
        """
        Start consuming messages and call handler for each

        Args:
            handler: Async function to handle each message

        Raises:
            RuntimeError: If consumer not started
        """
        if self._consumer is None:
            raise RuntimeError("Consumer not started. Call start() first.")

        try:
            async for msg in self._consumer:
                if not self._running:
                    break

                try:
                    await handler(msg.value)
                    logger.debug(
                        f"Processed message from {msg.topic}, "
                        f"partition={msg.partition}, offset={msg.offset}"
                    )
                except Exception as e:
                    logger.error(
                        f"Error handling message from {msg.topic}: {e}",
                        exc_info=True
                    )
        except asyncio.CancelledError:
            logger.info("Consumer loop cancelled")
            raise

    async def consume_in_background(
        self, handler: Callable[[Dict[str, Any]], None]
    ) -> None:
        """
        Start consuming messages in background task

        Args:
            handler: Async function to handle each message
        """
        self._task = asyncio.create_task(self.consume(handler))

    @property
    def is_running(self) -> bool:
        """Check if consumer is running"""
        return self._running and self._consumer is not None

    @property
    def is_connected(self) -> bool:
        """Check if consumer is connected"""
        return self._consumer is not None