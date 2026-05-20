"""
F00: Kafka消费者模块 (占位)

生产模式下的Kafka消费者实现。
需要kafka-python库和Kafka服务器。
"""


class KafkaConsumer:
    """
    Kafka消费者 (生产模式)

    当前为占位实现，实际消费逻辑需要kafka-python。
    """

    def __init__(self, config, event_type: str, handler):
        self._config = config
        self._event_type = event_type
        self._handler = handler
        self._running = False

    def start(self):
        """开始消费"""
        self._running = True

    def stop(self):
        """停止消费"""
        self._running = False
