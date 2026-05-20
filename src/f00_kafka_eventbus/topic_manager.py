"""
Kafka Topic Manager - creates and manages topics
"""

from aiokafka.admin import AIOKafkaAdminClient, NewTopic
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class KafkaTopicManager:
    """
    Kafka Topic Manager for creating and managing topics

    Features:
    - Automatic topic creation
    - Configurable partitions and replication
    - Error handling for existing topics
    """

    TOPICS: Dict[str, Dict[str, Any]] = {
        "chapter_events": {"partitions": 3, "replicas": 1},
        "review_events": {"partitions": 3, "replicas": 1},
        "security_events": {"partitions": 3, "replicas": 1},
        "audit_events": {"partitions": 3, "replicas": 1},
        "generation_tasks": {"partitions": 5, "replicas": 1},
        "dlq": {"partitions": 1, "replicas": 1},
    }

    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        self.bootstrap_servers = bootstrap_servers
        self._admin: Optional[AIOKafkaAdminClient] = None

    async def create_topics(self, topics: Optional[List[dict]] = None) -> None:
        """
        Create topics if they don't exist

        Args:
            topics: List of topic configs. If None, uses TOPICS class variable.
                    Each config should have: name, partitions (optional), replicas (optional)
        """
        topics_to_create = topics or self._get_default_topics()

        if not topics_to_create:
            logger.info("No topics to create")
            return

        self._admin = AIOKafkaAdminClient(
            bootstrap_servers=self.bootstrap_servers
        )
        await self._admin.start()

        try:
            new_topics = [
                NewTopic(
                    name=t["name"],
                    num_partitions=t.get("partitions", 3),
                    replication_factor=t.get("replicas", 1),
                )
                for t in topics_to_create
            ]

            await self._admin.create_topics(new_topics)
            logger.info(f"Created {len(new_topics)} topics: {[t.name for t in new_topics]}")

        except Exception as e:
            if "TopicExistsException" in str(type(e).__name__) or "TOPIC_ALREADY_EXISTS" in str(e):
                logger.info("Some topics already exist, skipping creation")
            else:
                logger.error(f"Error creating topics: {e}")
                raise
        finally:
            await self._admin.close()
            self._admin = None

    async def delete_topics(self, topic_names: List[str]) -> None:
        """
        Delete topics

        Args:
            topic_names: List of topic names to delete
        """
        if not topic_names:
            return

        self._admin = AIOKafkaAdminClient(
            bootstrap_servers=self.bootstrap_servers
        )
        await self._admin.start()

        try:
            await self._admin.delete_topics(topic_names)
            logger.info(f"Deleted topics: {topic_names}")
        except Exception as e:
            logger.error(f"Error deleting topics: {e}")
            raise
        finally:
            await self._admin.close()
            self._admin = None

    async def list_topics(self) -> List[str]:
        """
        List all topics

        Returns:
            List of topic names
        """
        self._admin = AIOKafkaAdminClient(
            bootstrap_servers=self.bootstrap_servers
        )
        await self._admin.start()

        try:
            cluster_metadata = await self._admin._client._wait_on_metadata()
            topics = list(cluster_metadata.topics.keys())
            return topics
        finally:
            await self._admin.close()
            self._admin = None

    def _get_default_topics(self) -> List[dict]:
        """Get default topic configurations"""
        return [
            {"name": name, **config}
            for name, config in self.TOPICS.items()
        ]

    @classmethod
    def get_standard_topics(cls) -> Dict[str, Dict[str, Any]]:
        """Get standard topic definitions"""
        return cls.TOPICS.copy()

    @classmethod
    def get_topic_config(cls, topic_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific topic"""
        return cls.TOPICS.get(topic_name)