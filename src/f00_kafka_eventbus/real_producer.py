"""
Real Kafka Producer using aiokafka
"""

import json
import logging
from typing import Any

from aiokafka import AIOKafkaProducer

logger = logging.getLogger(__name__)


class RealKafkaProducer:
    """
    Real Kafka Producer using aiokafka

    Features:
    - Async message production
    - Configurable acks and compression
    - Automatic serialization
    - Connection management
    - Retry mechanism with exponential backoff
    - Idempotent producer for exactly-once semantics
    """

    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        client_id: str = "textbook-producer",
        acks: str = "all",
        compression: str = "gzip",
        # KAFKA-001: Retry configuration
        retries: int = 3,
        retry_backoff_ms: int = 100,
        # KAFKA-002: Idempotence configuration
        enable_idempotence: bool = True,
        # KAFKA-004: Additional producer configs
        max_in_flight_requests_per_connection: int = 5,
        request_timeout_ms: int = 30000,
        max_batch_size: int = 16384,
    ):
        self.bootstrap_servers = bootstrap_servers
        self.client_id = client_id
        self.acks = acks
        self.compression = compression
        # KAFKA-001: Store retry config for reference
        self.retries = retries
        self.retry_backoff_ms = retry_backoff_ms
        self.enable_idempotence = enable_idempotence
        self.max_in_flight_requests_per_connection = max_in_flight_requests_per_connection
        self.request_timeout_ms = request_timeout_ms
        self.max_batch_size = max_batch_size
        self._producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        """Start the producer and establish connection to Kafka"""
        if self._producer is not None:
            logger.warning("Producer already started")
            return

        self._producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            client_id=self.client_id,
            acks=self.acks,
            compression_type=self.compression,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
            # KAFKA-001: Configure retries
            retries=self.retries,
            retry_backoff_ms=self.retry_backoff_ms,
            # KAFKA-002: Enable idempotence for exactly-once semantics
            enable_idempotence=self.enable_idempotence,
            # Additional reliability configs
            max_in_flight_requests_per_connection=self.max_in_flight_requests_per_connection,
            request_timeout_ms=self.request_timeout_ms,
            max_batch_size=self.max_batch_size,
        )
        await self._producer.start()
        logger.info(
            f"Kafka producer started, connected to {self.bootstrap_servers}, "
            f"idempotence={self.enable_idempotence}, retries={self.retries}"
        )

    async def stop(self) -> None:
        """Stop the producer and close connection"""
        if self._producer is None:
            return

        await self._producer.stop()
        self._producer = None
        logger.info("Kafka producer stopped")

    async def send(
        self,
        topic: str,
        value: dict[str, Any],
        key: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Send message to Kafka topic with retry logic

        Args:
            topic: Target topic name
            value: Message payload (dict)
            key: Optional message key for partitioning
            headers: Optional message headers

        Returns:
            Dict with send status, message_key, and any error info

        Raises:
            RuntimeError: If producer not started
        """
        if self._producer is None:
            raise RuntimeError("Producer not started. Call start() first.")

        headers_list = [(k, v.encode("utf-8")) for k, v in (headers or {}).items()]
        last_error = None

        # INF-002: Add retry logic with exponential backoff
        for attempt in range(self.retries + 1):
            try:
                await self._producer.send_and_wait(
                    topic,
                    value=value,
                    key=key,
                    headers=headers_list,
                )
                logger.debug(f"Message sent to topic {topic}, key={key}")
                return {
                    "success": True,
                    "key": key,
                    "topic": topic,
                    "attempt": attempt + 1,
                }
            except Exception as e:
                last_error = e
                if attempt < self.retries:
                    # Exponential backoff
                    delay = (self.retry_backoff_ms / 1000) * (2 ** attempt)
                    logger.warning(
                        f"Send attempt {attempt + 1} failed for topic {topic}, key={key}: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    import asyncio
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"All {self.retries + 1} send attempts failed for topic {topic}, key={key}: {e}"
                    )

        # All retries exhausted
        return {
            "success": False,
            "key": key,
            "topic": topic,
            "error": str(last_error),
            "attempt": self.retries + 1,
        }

    async def send_batch(
        self,
        topic: str,
        messages: list
    ) -> dict[str, Any]:
        """
        Send batch of messages to Kafka topic

        INF-001: Returns detailed status for each message so caller can handle
        partial failures appropriately, rather than throwing exceptions that
        leave previously sent messages in an inconsistent state.

        Args:
            topic: Target topic name
            messages: List of messages, each with 'value' and optional 'key'

        Returns:
            Dict with detailed status including per-message results:
            {
                "total": int,
                "succeeded": int,
                "failed": int,
                "results": [{"key": ..., "success": bool, "error": ...}, ...]
            }
        """
        if self._producer is None:
            raise RuntimeError("Producer not started. Call start() first.")

        results = {
            "total": len(messages),
            "succeeded": 0,
            "failed": 0,
            "results": [],  # INF-001: Detailed per-message status
        }

        for msg in messages:
            msg_key = msg.get("key")
            try:
                # Use the retry-enabled send method
                send_result = await self.send(
                    topic=topic,
                    value=msg["value"],
                    key=msg_key,
                )
                if send_result.get("success"):
                    results["succeeded"] += 1
                    results["results"].append({
                        "key": msg_key,
                        "success": True,
                    })
                else:
                    results["failed"] += 1
                    results["results"].append({
                        "key": msg_key,
                        "success": False,
                        "error": send_result.get("error", "Unknown error"),
                    })
                    logger.warning(
                        f"Batch send partial failure: {results['succeeded']}/{results['total']} "
                        f"succeeded so far"
                    )
            except Exception as e:
                results["failed"] += 1
                results["results"].append({
                    "key": msg_key,
                    "success": False,
                    "error": str(e),
                })
                logger.error(
                    f"Failed to send batch message to {topic}, key={msg_key}: {e}"
                )
                logger.warning(
                    f"Batch send partial failure: {results['succeeded']}/{results['total']} "
                    f"succeeded so far"
                )

        logger.info(
            f"Batch of {results['total']} messages sent to {topic}: "
            f"{results['succeeded']} succeeded, {results['failed']} failed"
        )

        # Return detailed results instead of raising exception
        # Caller is responsible for handling partial failures
        return results

    async def flush(self) -> None:
        """Flush any pending messages"""
        if self._producer:
            await self._producer.flush()

    @property
    def is_connected(self) -> bool:
        """Check if producer is connected"""
        return self._producer is not None
