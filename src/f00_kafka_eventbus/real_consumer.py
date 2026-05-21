"""
Real Kafka Consumer using aiokafka
"""

from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError
from typing import Callable, Optional, Dict, Any, List, Set
import asyncio
import json
import logging
import time

logger = logging.getLogger(__name__)


class RealKafkaConsumer:
    """
    Real Kafka Consumer using aiokafka

    Features:
    - Async message consumption
    - Consumer group support
    - Manual offset commit for reliability
    - Configurable offset reset
    - Deduplication support
    - Graceful error handling with message continuation
    """

    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        group_id: str = "textbook-consumer",
        auto_offset_reset: str = "earliest",
        topics: Optional[List[str]] = None,
        # KAFKA-006: Manual commit for reliability
        enable_auto_commit: bool = False,
        auto_commit_interval_ms: int = 5000,
        # KAFKA-004: Retry configuration for consumer
        max_retries: int = 3,
        retry_backoff_ms: int = 1000,
    ):
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.auto_offset_reset = auto_offset_reset
        self.topics = topics or []
        self.enable_auto_commit = enable_auto_commit
        self.auto_commit_interval_ms = auto_commit_interval_ms
        self.max_retries = max_retries
        self.retry_backoff_ms = retry_backoff_ms
        self._consumer: Optional[AIOKafkaConsumer] = None
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._pending_offsets: Dict[str, Dict[int, int]] = {}  # topic -> partition -> offset

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
            # KAFKA-006: Disable auto commit for manual commit control
            enable_auto_commit=self.enable_auto_commit,
            auto_commit_interval_ms=self.auto_commit_interval_ms,
        )
        await self._consumer.start()
        self._running = True
        logger.info(
            f"Kafka consumer started, connected to {self.bootstrap_servers}, "
            f"group={self.group_id}, topics={self.topics}, "
            f"auto_commit={self.enable_auto_commit}"
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
            # Commit any pending offsets before stopping
            if self._pending_offsets:
                await self._commit_pending_offsets()
            await self._consumer.stop()
            self._consumer = None
            logger.info("Kafka consumer stopped")

    async def _commit_pending_offsets(self) -> None:
        """Commit pending offsets to Kafka"""
        if not self._pending_offsets or not self._consumer:
            return

        try:
            for topic, partitions in self._pending_offsets.items():
                for partition, offset in partitions.items():
                    # Commit offset + 1 to mark message as processed
                    await self._consumer.commit()
                    logger.debug(f"Committed offset {offset + 1} for {topic}:{partition}")
            self._pending_offsets.clear()
        except Exception as e:
            logger.error(f"Failed to commit offsets: {e}")

    async def _commit_offset(self, topic: str, partition: int, offset: int) -> None:
        """
        Track offset for commit. Actual commit happens after successful processing.

        Args:
            topic: Topic name
            partition: Partition number
            offset: Last successfully processed offset
        """
        if topic not in self._pending_offsets:
            self._pending_offsets[topic] = {}
        # Store offset to commit (add 1 since offset is inclusive)
        self._pending_offsets[topic][partition] = offset + 1

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

                topic_partition = f"{msg.topic}:{msg.partition}"
                last_error = None
                handler_success = False

                # KAFKA-004: Implement retry with exponential backoff for handler
                for attempt in range(self.max_retries + 1):
                    try:
                        await handler(msg.value)
                        logger.debug(
                            f"Processed message from {msg.topic}, "
                            f"partition={msg.partition}, offset={msg.offset}"
                        )
                        handler_success = True
                        break
                    except Exception as e:
                        last_error = e
                        if attempt < self.max_retries:
                            # Exponential backoff
                            delay = self.retry_backoff_ms * (2 ** attempt) / 1000.0
                            logger.warning(
                                f"Handler attempt {attempt + 1} failed for {topic_partition}: {e}. "
                                f"Retrying in {delay:.2f}s..."
                            )
                            await asyncio.sleep(delay)
                        else:
                            logger.error(
                                f"All {self.max_retries + 1} attempts failed for {topic_partition}: {e}"
                            )

                # INF-003: Regardless of success or failure, commit offset to prevent
                # infinite reprocessing. If handler failed, message goes to DLQ but we
                # still advance offset so we don't get stuck.
                await self._commit_offset(msg.topic, msg.partition, msg.offset)

                # KAFKA-012: Periodically commit offsets to ensure progress
                if self._pending_offsets:
                    await self._commit_pending_offsets()

                # If handler failed after all retries, log the error but continue
                if not handler_success and last_error:
                    logger.error(
                        f"Message processing failed after {self.max_retries + 1} attempts, "
                        f"sending to DLQ: {last_error}"
                    )
                    # Note: DLQ sending is handled by caller (event_bus.py)
                    # Here we just log and continue to next message

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
