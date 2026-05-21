"""
F00: Kafka生产者配置模块

定义Kafka连接配置。
生产模式需要kafka-python库和Kafka服务器。
"""

from dataclasses import dataclass


@dataclass
class KafkaConfig:
    """
    Kafka连接配置

    Attributes:
        bootstrap_servers: Kafka broker地址
        topic_prefix: 主题前缀
        consumer_group: 消费者组名
    """

    bootstrap_servers: str = "localhost:9092"
    topic_prefix: str = "textbook"
    consumer_group: str = "textbook-system"

    def get_topic(self, event_type: str) -> str:
        """获取完整主题名"""
        return f"{self.topic_prefix}.{event_type}"
