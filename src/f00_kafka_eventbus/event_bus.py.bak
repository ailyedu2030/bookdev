"""
F00: 事件总线工厂

根据配置创建对应的事件总线实例。
无Kafka时自动使用Mock总线。
"""

from typing import Optional


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

        Args:
            event_type: 事件类型
            handler: 事件处理函数
            max_retries: 失败最大重试次数
            retry_delay: 重试间隔(秒)

        Returns:
            subscription_id: 订阅ID
        """
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

    async def start_consuming(self) -> None:
        """开始消费消息"""
        from f00_kafka_eventbus.real_consumer import RealKafkaConsumer

        self._running = True

        for topic, subs in self._subscribers.items():
            consumer = RealKafkaConsumer(
                bootstrap_servers=self._bootstrap_servers,
                group_id=self._consumer_group,
                topics=[topic],
            )
            await consumer.start()

            async def create_handler(sub_list):
                async def handler(msg):
                    for sub in sub_list:
                        try:
                            await sub["handler"](msg)
                        except Exception as e:
                            if sub["max_retries"] > 0:
                                pass
                            else:
                                if self._dlq_handler:
                                    await self._dlq_handler.send_to_dlq(
                                        msg, e, sub["handler"].__name__
                                    )
                return handler

            self._consumers[topic] = consumer
            await consumer.consume_in_background(await create_handler(subs))

    async def stop_consuming(self) -> None:
        """停止消费消息"""
        self._running = False
        for consumer in self._consumers.values():
            await consumer.stop()
        self._consumers.clear()
