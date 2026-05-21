# F00: Kafka事件总线系统

from f00_kafka_eventbus.event_bus import RealEventBus, create_event_bus
from f00_kafka_eventbus.event_definitions import EVENTS, Event, InvalidEventTypeError
from f00_kafka_eventbus.mock_bus import MockEventBus
from f00_kafka_eventbus.producer import KafkaConfig

try:
    from f00_kafka_eventbus.real_producer import RealKafkaProducer
except ImportError:
    RealKafkaProducer = None

try:
    from f00_kafka_eventbus.real_consumer import RealKafkaConsumer
except ImportError:
    RealKafkaConsumer = None

try:
    from f00_kafka_eventbus.topic_manager import KafkaTopicManager
except ImportError:
    KafkaTopicManager = None

try:
    from f00_kafka_eventbus.dlq_handler import DLQHandler, DLQMessage, RetryConfig
except ImportError:
    DLQHandler = None
    DLQMessage = None
    RetryConfig = None

__all__ = [
    "create_event_bus",
    "RealEventBus",
    "MockEventBus",
    "Event",
    "EVENTS",
    "InvalidEventTypeError",
    "KafkaConfig",
    "RealKafkaProducer",
    "RealKafkaConsumer",
    "KafkaTopicManager",
    "DLQHandler",
    "DLQMessage",
    "RetryConfig",
]
