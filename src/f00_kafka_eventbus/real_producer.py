"""
Real Kafka Producer using aiokafka
"""

from aiokafka import AIOKafkaProducer
from typing import Optional, Dict, Any
import json
import logging

logger = logging.getLogger(__name__)


class RealKafkaProducer:
    """
    Real Kafka Producer using aiokafka

    Features:
    - Async message production
    - Configurable acks and compression
    - Automatic serialization
    - Connection management
    """

    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        client_id: str = "textbook-producer",
        acks: str = "all",
        compression: str = "gzip",
    ):
        self.bootstrap_servers = bootstrap_servers
        self.client_id = client_id
        self.acks = acks
        self.compression = compression
        self._producer: Optional[AIOKafkaProducer] = None

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
        )
        await self._producer.start()
        logger.info(f"Kafka producer started, connected to {self.bootstrap_servers}")

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
        value: Dict[str, Any],
        key: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Send message to Kafka topic

        Args:
            topic: Target topic name
            value: Message payload (dict)
            key: Optional message key for partitioning
            headers: Optional message headers

        Raises:
            RuntimeError: If producer not started
        """
        if self._producer is None:
            raise RuntimeError("Producer not started. Call start() first.")

        headers_list = [(k, v.encode("utf-8")) for k, v in (headers or {}).items()]

        try:
            await self._producer.send_and_wait(
                topic,
                value=value,
                key=key,
                headers=headers_list,
            )
            logger.debug(f"Message sent to topic {topic}, key={key}")
        except Exception as e:
            logger.error(f"Failed to send message to {topic}: {e}")
            raise

    async def send_batch(self, topic: str, messages: list) -> None:
        """
        Send batch of messages to Kafka topic

        Args:
            topic: Target topic name
            messages: List of messages, each with 'value' and optional 'key'

        Raises:
            RuntimeError: If producer not started
        """
        if self._producer is None:
            raise RuntimeError("Producer not started. Call start() first.")

        for msg in messages:
            try:
                await self._producer.send_and_wait(
                    topic,
                    value=msg["value"],
                    key=msg.get("key"),
                )
            except Exception as e:
                logger.error(f"Failed to send batch message to {topic}: {e}")
                raise

        logger.debug(f"Batch of {len(messages)} messages sent to {topic}")

    async def flush(self) -> None:
        """Flush any pending messages"""
        if self._producer:
            await self._producer.flush()

    @property
    def is_connected(self) -> bool:
        """Check if producer is connected"""
        return self._producer is not None