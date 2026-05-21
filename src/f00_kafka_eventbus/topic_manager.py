"""
Kafka Topic Manager - creates and manages topics
"""

import asyncio
import logging
from typing import Any

from aiokafka.admin import AIOKafkaAdminClient, NewTopic

logger = logging.getLogger(__name__)


class KafkaTopicManager:
    """
    Kafka Topic Manager for creating and managing topics

    Features:
    - Automatic topic creation
    - Configurable partitions and replication
    - Error handling for existing topics
    - Support for ordered topics (single partition)
    - High availability configuration
    - Connection reuse for efficiency (INF-004)
    """

    # KAFKA-009: Added 'ordered' flag for topics that require message ordering
    # KAFKA-011: Changed default replicas to 2 for production HA
    TOPICS: dict[str, dict[str, Any]] = {
        "chapter_events": {
            "partitions": 3,
            "replicas": 2,
            "ordered": False,  # Can be split across partitions, order not critical
        },
        "review_events": {
            "partitions": 3,
            "replicas": 2,
            "ordered": False,
        },
        "security_events": {
            "partitions": 1,  # KAFKA-009: Single partition for ordering guarantee
            "replicas": 2,
            "ordered": True,  # Security events must maintain order
        },
        "audit_events": {
            "partitions": 1,  # KAFKA-009: Single partition for audit trail ordering
            "replicas": 2,
            "ordered": True,
        },
        "generation_tasks": {
            "partitions": 5,
            "replicas": 2,
            "ordered": False,  # Tasks can be parallelized across partitions
        },
        "dlq": {
            "partitions": 1,
            "replicas": 2,  # KAFKA-011: DLQ should also be reliable
            "ordered": True,  # DLQ ordering can help with retry sequencing
        },
    }

    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        self.bootstrap_servers = bootstrap_servers
        # INF-004: Reuse admin client instead of creating/destroying per operation
        self._admin: AIOKafkaAdminClient | None = None
        self._admin_lock = asyncio.Lock()

    async def _get_admin(self) -> AIOKafkaAdminClient:
        """
        Get or create admin client with connection reuse.

        Returns:
            AIOKafkaAdminClient instance
        """
        if self._admin is None:
            async with self._admin_lock:
                # Double-check after acquiring lock
                if self._admin is None:
                    self._admin = AIOKafkaAdminClient(bootstrap_servers=self.bootstrap_servers)
                    await self._admin.start()
                    logger.debug(f"Admin client created for {self.bootstrap_servers}")
        return self._admin

    async def _release_admin(self) -> None:
        """Release admin client without closing (for connection reuse)"""
        # For aiokafka, we keep the connection alive for reuse
        # The admin client doesn't have a pause/resume mechanism,
        # so we just keep it open and rely on TCP keepalive
        pass

    async def create_topics(self, topics: list[dict] | None = None) -> None:
        """
        Create topics if they don't exist

        Args:
            topics: List of topic configs. If None, uses TOPICS class variable.
                    Each config should have: name, partitions (optional), replicas (optional)
                    and ordered (optional).
        """
        topics_to_create = topics or self._get_default_topics()

        if not topics_to_create:
            logger.info("No topics to create")
            return

        admin = await self._get_admin()

        try:
            new_topics = []
            for t in topics_to_create:
                name = t["name"]
                # KAFKA-009: If ordered=True, force single partition regardless of config
                partitions = 1 if t.get("ordered", False) else t.get("partitions", 3)
                replicas = t.get("replicas", 2)  # KAFKA-011: Default to 2 for HA

                topic = NewTopic(
                    name=name,
                    num_partitions=partitions,
                    replication_factor=replicas,
                )
                new_topics.append(topic)

                if t.get("ordered", False):
                    logger.info(
                        f"Topic '{name}' configured for ordered delivery "
                        f"(partitions={partitions}, replicas={replicas})"
                    )

            await admin.create_topics(new_topics)
            logger.info(f"Created {len(new_topics)} topics: {[t.name for t in new_topics]}")

        except Exception as e:
            if "TopicExistsException" in str(type(e).__name__) or "TOPIC_ALREADY_EXISTS" in str(e):
                logger.info("Some topics already exist, skipping creation")
            else:
                logger.error(f"Error creating topics: {e}")
                raise
        # Note: We don't close admin client here to allow connection reuse (INF-004)

    async def delete_topics(self, topic_names: list[str]) -> None:
        """
        Delete topics

        Args:
            topic_names: List of topic names to delete
        """
        if not topic_names:
            return

        admin = await self._get_admin()

        try:
            await admin.delete_topics(topic_names)
            logger.info(f"Deleted topics: {topic_names}")
        except Exception as e:
            logger.error(f"Error deleting topics: {e}")
            raise

    async def list_topics(self) -> list[str]:
        """
        List all topics

        Returns:
            List of topic names
        """
        admin = await self._get_admin()

        try:
            cluster_metadata = await admin._client._wait_on_metadata()
            topics = list(cluster_metadata.topics.keys())
            return topics
        finally:
            # Keep admin connection alive for reuse (INF-004)
            pass

    async def close(self) -> None:
        """
        Close the admin client and release resources.

        Call this when done with topic management operations.
        """
        if self._admin is not None:
            async with self._admin_lock:
                if self._admin is not None:
                    await self._admin.close()
                    self._admin = None
                    logger.debug("Admin client closed")

    def _get_default_topics(self) -> list[dict]:
        """Get default topic configurations"""
        return [{"name": name, **config} for name, config in self.TOPICS.items()]

    @classmethod
    def get_standard_topics(cls) -> dict[str, dict[str, Any]]:
        """Get standard topic definitions"""
        return cls.TOPICS.copy()

    @classmethod
    def get_topic_config(cls, topic_name: str) -> dict[str, Any] | None:
        """Get configuration for a specific topic"""
        return cls.TOPICS.get(topic_name)

    @classmethod
    def is_topic_ordered(cls, topic_name: str) -> bool:
        """Check if a topic requires ordered delivery"""
        config = cls.TOPICS.get(topic_name, {})
        return config.get("ordered", False)
