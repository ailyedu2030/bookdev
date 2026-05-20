"""
F00: RealKafkaProducer Tests

TDD Phase RED: Tests for RealKafkaProducer
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass


@dataclass
class MockProducer:
    """Mock AIOKafkaProducer"""
    bootstrap_servers: str = ""
    client_id: str = ""
    acks: str = ""
    compression_type: str = ""

    async def start(self):
        pass

    async def stop(self):
        pass

    async def send_and_wait(self, topic, value=None, key=None, headers=None):
        pass

    async def flush(self):
        pass


class TestRealKafkaProducer:
    """RealKafkaProducer 测试"""

    def test_producer_initialization(self):
        """F00-T100: Producer可以使用默认参数初始化"""
        from f00_kafka_eventbus.real_producer import RealKafkaProducer

        producer = RealKafkaProducer()
        assert producer.bootstrap_servers == "localhost:9092"
        assert producer.client_id == "textbook-producer"
        assert producer.acks == "all"
        assert producer.compression == "gzip"
        assert producer._producer is None

    def test_producer_with_custom_config(self):
        """F00-T101: Producer可以使用自定义参数初始化"""
        from f00_kafka_eventbus.real_producer import RealKafkaProducer

        producer = RealKafkaProducer(
            bootstrap_servers="kafka:9092",
            client_id="test-client",
            acks="one",
            compression="lz4",
        )
        assert producer.bootstrap_servers == "kafka:9092"
        assert producer.client_id == "test-client"
        assert producer.acks == "one"
        assert producer.compression == "lz4"

    def test_is_connected_false_when_not_started(self):
        """F00-T102: 未启动时is_connected返回False"""
        from f00_kafka_eventbus.real_producer import RealKafkaProducer

        producer = RealKafkaProducer()
        assert producer.is_connected is False

    def test_is_connected_true_when_started(self):
        """F00-T103: 启动后is_connected返回True"""
        from f00_kafka_eventbus.real_producer import RealKafkaProducer

        producer = RealKafkaProducer()

        with patch("f00_kafka_eventbus.real_producer.AIOKafkaProducer") as mock_class:
            mock_instance = AsyncMock()
            mock_class.return_value = mock_instance

            import asyncio
            asyncio.run(producer.start())

            assert producer.is_connected is True

    @pytest.mark.asyncio
    async def test_start_creates_producer(self):
        """F00-T104: start()创建AIOKafkaProducer实例"""
        from f00_kafka_eventbus.real_producer import RealKafkaProducer

        producer = RealKafkaProducer(bootstrap_servers="kafka:9092", client_id="test")

        with patch("f00_kafka_eventbus.real_producer.AIOKafkaProducer") as mock_class:
            mock_instance = AsyncMock()
            mock_class.return_value = mock_instance

            await producer.start()

            mock_class.assert_called_once()
            call_kwargs = mock_class.call_args.kwargs
            assert call_kwargs["bootstrap_servers"] == "kafka:9092"
            assert call_kwargs["client_id"] == "test"
            assert call_kwargs["acks"] == "all"
            assert call_kwargs["compression_type"] == "gzip"

    @pytest.mark.asyncio
    async def test_stop_closes_producer(self):
        """F00-T105: stop()关闭producer"""
        from f00_kafka_eventbus.real_producer import RealKafkaProducer

        producer = RealKafkaProducer()

        with patch("f00_kafka_eventbus.real_producer.AIOKafkaProducer") as mock_class:
            mock_instance = AsyncMock()
            mock_class.return_value = mock_instance

            await producer.start()
            await producer.stop()

            mock_instance.stop.assert_called_once()
            assert producer._producer is None

    @pytest.mark.asyncio
    async def test_stop_when_not_started_is_noop(self):
        """F00-T106: 未启动时stop()是空操作"""
        from f00_kafka_eventbus.real_producer import RealKafkaProducer

        producer = RealKafkaProducer()
        await producer.stop()
        assert producer._producer is None

    @pytest.mark.asyncio
    async def test_send_raises_when_not_started(self):
        """F00-T107: 未启动时send()抛出RuntimeError"""
        from f00_kafka_eventbus.real_producer import RealKafkaProducer

        producer = RealKafkaProducer()

        with pytest.raises(RuntimeError, match="Producer not started"):
            await producer.send("test-topic", {"message": "test"})

    @pytest.mark.asyncio
    async def test_send_calls_send_and_wait(self):
        """F00-T108: send()调用producer的send_and_wait"""
        from f00_kafka_eventbus.real_producer import RealKafkaProducer

        producer = RealKafkaProducer()

        with patch("f00_kafka_eventbus.real_producer.AIOKafkaProducer") as mock_class:
            mock_instance = AsyncMock()
            mock_class.return_value = mock_instance

            await producer.start()
            await producer.send("test-topic", {"message": "hello"}, key="key-1")

            mock_instance.send_and_wait.assert_called_once()
            call_args = mock_instance.send_and_wait.call_args
            assert call_args[0][0] == "test-topic"
            assert call_args[1]["value"] == {"message": "hello"}
            assert call_args[1]["key"] == "key-1"

    @pytest.mark.asyncio
    async def test_send_with_headers(self):
        """F00-T109: send()支持headers参数"""
        from f00_kafka_eventbus.real_producer import RealKafkaProducer

        producer = RealKafkaProducer()

        with patch("f00_kafka_eventbus.real_producer.AIOKafkaProducer") as mock_class:
            mock_instance = AsyncMock()
            mock_class.return_value = mock_instance

            await producer.start()
            await producer.send(
                "test-topic",
                {"message": "hello"},
                headers={"content-type": "application/json"},
            )

            call_args = mock_instance.send_and_wait.call_args
            headers_list = call_args[1]["headers"]
            assert len(headers_list) == 1
            assert headers_list[0][0] == "content-type"

    @pytest.mark.asyncio
    async def test_send_batch_raises_when_not_started(self):
        """F00-T110: send_batch()未启动时抛出RuntimeError"""
        from f00_kafka_eventbus.real_producer import RealKafkaProducer

        producer = RealKafkaProducer()

        with pytest.raises(RuntimeError, match="Producer not started"):
            await producer.send_batch("test-topic", [{"value": {"msg": "test"}}])

    @pytest.mark.asyncio
    async def test_send_batch_sends_all_messages(self):
        """F00-T111: send_batch()发送所有消息"""
        from f00_kafka_eventbus.real_producer import RealKafkaProducer

        producer = RealKafkaProducer()

        with patch("f00_kafka_eventbus.real_producer.AIOKafkaProducer") as mock_class:
            mock_instance = AsyncMock()
            mock_class.return_value = mock_instance

            messages = [
                {"value": {"msg": "1"}, "key": "k1"},
                {"value": {"msg": "2"}, "key": "k2"},
            ]

            await producer.start()
            await producer.send_batch("test-topic", messages)

            assert mock_instance.send_and_wait.call_count == 2

    @pytest.mark.asyncio
    async def test_flush_calls_producer_flush(self):
        """F00-T112: flush()调用producer.flush()"""
        from f00_kafka_eventbus.real_producer import RealKafkaProducer

        producer = RealKafkaProducer()

        with patch("f00_kafka_eventbus.real_producer.AIOKafkaProducer") as mock_class:
            mock_instance = AsyncMock()
            mock_class.return_value = mock_instance

            await producer.start()
            await producer.flush()

            mock_instance.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_is_idempotent(self):
        """F00-T113: 多次start()是幂等的"""
        from f00_kafka_eventbus.real_producer import RealKafkaProducer

        producer = RealKafkaProducer()

        with patch("f00_kafka_eventbus.real_producer.AIOKafkaProducer") as mock_class:
            mock_instance = AsyncMock()
            mock_class.return_value = mock_instance

            await producer.start()
            await producer.start()

            mock_instance.start.assert_called_once()
