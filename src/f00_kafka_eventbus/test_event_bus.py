"""
F00: Kafka事件总线 - TDD RED阶段测试

测试覆盖:
- 事件创建与序列化
- Mock总线发布/订阅
- 多消费者并行
- 事件顺序保证
- 死信队列
- 事件溯源日志
- 至少一次语义重试
- 错误处理与重连
- 工厂模式总线切换
"""

import pytest
import json
import time
import threading
from datetime import datetime
from dataclasses import asdict


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def mock_bus():
    """创建Mock事件总线"""
    from f00_kafka_eventbus.mock_bus import MockEventBus
    bus = MockEventBus()
    yield bus
    bus.shutdown()


@pytest.fixture
def collected_events():
    """收集事件的fixture"""
    events = []
    return events


# ============================================================
# T001-T003: 事件定义
# ============================================================

class TestEventDefinitions:
    """事件类型定义测试"""

    def test_event_has_required_fields(self):
        """F00-T001: 事件必须有id, type, timestamp, payload字段"""
        from f00_kafka_eventbus.event_definitions import Event

        event = Event(
            event_id="evt-001",
            event_type="chapter.created",
            timestamp=datetime.utcnow(),
            payload={"chapter_id": "ch1", "title": "第一章"},
        )

        assert event.event_id == "evt-001"
        assert event.event_type == "chapter.created"
        assert isinstance(event.timestamp, datetime)
        assert event.payload == {"chapter_id": "ch1", "title": "第一章"}

    def test_event_id_auto_generated(self):
        """F00-T001b: event_id未提供时自动生成UUID"""
        from f00_kafka_eventbus.event_definitions import Event

        event = Event(
            event_type="chapter.created",
            timestamp=datetime.utcnow(),
            payload={"data": "test"},
        )

        assert event.event_id is not None
        assert len(event.event_id) > 0

    def test_event_serialization_to_json(self):
        """F00-T002: 事件可序列化为JSON"""
        from f00_kafka_eventbus.event_definitions import Event

        event = Event(
            event_id="evt-001",
            event_type="chapter.created",
            timestamp=datetime(2025, 6, 1, 12, 0, 0),
            payload={"chapter_id": "ch1"},
        )

        json_str = event.to_json()
        data = json.loads(json_str)

        assert data["event_id"] == "evt-001"
        assert data["event_type"] == "chapter.created"
        assert data["payload"] == {"chapter_id": "ch1"}
        assert data["timestamp"] is not None

    def test_event_deserialization_from_json(self):
        """F00-T002b: 事件可从JSON反序列化"""
        from f00_kafka_eventbus.event_definitions import Event

        original = Event(
            event_id="evt-001",
            event_type="chapter.created",
            timestamp=datetime(2025, 6, 1, 12, 0, 0),
            payload={"chapter_id": "ch1"},
        )

        json_str = original.to_json()
        restored = Event.from_json(json_str)

        assert restored.event_id == original.event_id
        assert restored.event_type == original.event_type
        assert restored.payload == original.payload

    def test_all_event_types_defined(self):
        """F00-T003: 所有事件类型已预定义"""
        from f00_kafka_eventbus.event_definitions import EVENTS

        expected_events = {
            "chapter.created",
            "chapter.content_ready",
            "chapter.reviewed",
            "chapter.published",
            "security.violation",
            "quality.score_updated",
            "pipeline.stage_changed",
        }

        assert set(EVENTS) == expected_events

    def test_event_type_validation(self):
        """F00-T003b: 事件类型必须是预定义值"""
        from f00_kafka_eventbus.event_definitions import (
            Event,
            InvalidEventTypeError,
        )

        # 有效类型
        event = Event(
            event_type="chapter.created",
            timestamp=datetime.utcnow(),
            payload={},
        )
        assert event.event_type == "chapter.created"

        # 无效类型
        with pytest.raises(InvalidEventTypeError):
            Event(
                event_type="invalid.type",
                timestamp=datetime.utcnow(),
                payload={},
            )


# ============================================================
# T004-T007: Mock总线 发布/订阅
# ============================================================

class TestMockBusPublishSubscribe:
    """Mock总线基础发布/订阅测试"""

    def test_publish_and_subscribe_single_event(self, mock_bus):
        """F00-T004: 发布事件后订阅者能收到"""
        from f00_kafka_eventbus.event_definitions import Event

        received = []

        def handler(event: Event):
            received.append(event)

        mock_bus.subscribe("chapter.created", handler)
        event = Event(
            event_type="chapter.created",
            timestamp=datetime.utcnow(),
            payload={"chapter_id": "ch1"},
        )
        mock_bus.publish(event)

        # 给异步处理一点时间
        time.sleep(0.1)

        assert len(received) == 1
        assert received[0].event_id == event.event_id
        assert received[0].payload == {"chapter_id": "ch1"}

    def test_publish_without_subscribers_no_error(self, mock_bus):
        """F00-T004b: 无订阅者时发布不报错"""
        from f00_kafka_eventbus.event_definitions import Event

        event = Event(
            event_type="chapter.created",
            timestamp=datetime.utcnow(),
            payload={},
        )

        # 不应抛出异常
        mock_bus.publish(event)

    def test_multiple_subscribers_same_event(self, mock_bus):
        """F00-T005: 同一事件多个消费者并行接收"""
        from f00_kafka_eventbus.event_definitions import Event

        received_1 = []
        received_2 = []

        mock_bus.subscribe("chapter.created", lambda e: received_1.append(e))
        mock_bus.subscribe("chapter.created", lambda e: received_2.append(e))

        event = Event(
            event_type="chapter.created",
            timestamp=datetime.utcnow(),
            payload={"chapter_id": "ch1"},
        )
        mock_bus.publish(event)

        time.sleep(0.1)

        assert len(received_1) == 1
        assert len(received_2) == 1
        assert received_1[0].event_id == received_2[0].event_id

    def test_different_event_types_routed_correctly(self, mock_bus):
        """F00-T005b: 不同类型事件路由到正确的订阅者"""
        from f00_kafka_eventbus.event_definitions import Event

        created_received = []
        reviewed_received = []

        mock_bus.subscribe("chapter.created", lambda e: created_received.append(e))
        mock_bus.subscribe("chapter.reviewed", lambda e: reviewed_received.append(e))

        event1 = Event(
            event_type="chapter.created",
            timestamp=datetime.utcnow(),
            payload={"id": "ch1"},
        )
        event2 = Event(
            event_type="chapter.reviewed",
            timestamp=datetime.utcnow(),
            payload={"id": "ch2"},
        )

        mock_bus.publish(event1)
        mock_bus.publish(event2)

        time.sleep(0.1)

        assert len(created_received) == 1
        assert created_received[0].event_type == "chapter.created"
        assert len(reviewed_received) == 1
        assert reviewed_received[0].event_type == "chapter.reviewed"

    def test_subscribe_with_pattern_matching(self, mock_bus):
        """F00-T005c: 支持通配符模式匹配"""
        from f00_kafka_eventbus.event_definitions import Event

        received = []

        # 订阅所有chapter.*事件
        mock_bus.subscribe("chapter.*", received.append)

        mock_bus.publish(Event(
            event_type="chapter.created",
            timestamp=datetime.utcnow(),
            payload={},
        ))
        mock_bus.publish(Event(
            event_type="chapter.reviewed",
            timestamp=datetime.utcnow(),
            payload={},
        ))
        mock_bus.publish(Event(
            event_type="security.violation",
            timestamp=datetime.utcnow(),
            payload={},
        ))

        time.sleep(0.1)

        assert len(received) == 2

    def test_unsubscribe(self, mock_bus):
        """F00-T005d: 取消订阅后不再接收事件"""
        from f00_kafka_eventbus.event_definitions import Event

        received = []

        def handler(event: Event):
            received.append(event)

        sub_id = mock_bus.subscribe("chapter.created", handler)
        mock_bus.unsubscribe(sub_id)

        event = Event(
            event_type="chapter.created",
            timestamp=datetime.utcnow(),
            payload={},
        )
        mock_bus.publish(event)

        time.sleep(0.1)

        assert len(received) == 0


# ============================================================
# T006-T008: 事件顺序与并发
# ============================================================

class TestEventOrdering:
    """事件顺序保证测试"""

    def test_events_processed_in_order(self, mock_bus):
        """F00-T006: 同一topic事件按发布顺序处理"""
        from f00_kafka_eventbus.event_definitions import Event

        received = []

        mock_bus.subscribe("chapter.created", received.append)

        ids = ["a", "b", "c", "d", "e"]
        for i, eid in enumerate(ids):
            mock_bus.publish(Event(
                event_type="chapter.created",
                timestamp=datetime.utcnow(),
                payload={"order": i, "id": eid},
            ))

        time.sleep(0.3)

        assert len(received) == len(ids)
        for i, event in enumerate(received):
            assert event.payload["order"] == i

    def test_concurrent_publishing(self, mock_bus):
        """F00-T007: 并发发布不丢失事件"""
        from f00_kafka_eventbus.event_definitions import Event

        received = []
        received_lock = threading.Lock()

        def handler(event: Event):
            with received_lock:
                received.append(event)

        mock_bus.subscribe("chapter.created", handler)

        def publish_batch(count):
            for i in range(count):
                mock_bus.publish(Event(
                    event_type="chapter.created",
                    timestamp=datetime.utcnow(),
                    payload={"batch": count, "index": i},
                ))

        threads = []
        total = 50
        for _ in range(5):
            t = threading.Thread(target=publish_batch, args=(total // 5,))
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        time.sleep(0.3)

        assert len(received) == total


# ============================================================
# T009-T011: 死信队列
# ============================================================

class TestDeadLetterQueue:
    """死信队列测试"""

    def test_failed_event_goes_to_dlq(self, mock_bus):
        """F00-T009: 处理失败的事件进入死信队列"""
        from f00_kafka_eventbus.event_definitions import Event

        dlq_events = []

        def faulty_handler(event: Event):
            raise ValueError("模拟处理失败")

        def dlq_handler(event: Event):
            dlq_events.append(event)

        mock_bus.subscribe("chapter.created", faulty_handler)
        mock_bus.subscribe_dead_letter(dlq_handler)

        event = Event(
            event_type="chapter.created",
            timestamp=datetime.utcnow(),
            payload={"chapter_id": "ch1"},
        )
        mock_bus.publish(event)

        time.sleep(0.2)

        assert len(dlq_events) == 1
        # DLQ创建的是包装事件，检查原始事件ID在payload中
        assert dlq_events[0].payload["original_event_id"] == event.event_id

    def test_dlq_event_contains_error_info(self, mock_bus):
        """F00-T009b: 死信事件包含错误信息"""
        from f00_kafka_eventbus.event_definitions import Event

        dlq_event = None

        def faulty_handler(event: Event):
            raise RuntimeError("数据库连接超时")

        def dlq_handler(event: Event):
            nonlocal dlq_event
            dlq_event = event

        mock_bus.subscribe("chapter.content_ready", faulty_handler)
        mock_bus.subscribe_dead_letter(dlq_handler)

        event = Event(
            event_type="chapter.content_ready",
            timestamp=datetime.utcnow(),
            payload={"chapter_id": "ch1"},
        )
        mock_bus.publish(event)

        time.sleep(0.2)

        assert dlq_event is not None
        assert "error" in dlq_event.payload or dlq_event.payload.get("error_type") is not None

    def test_multiple_dlq_handlers(self, mock_bus):
        """F00-T009c: 多个死信队列处理器"""
        from f00_kafka_eventbus.event_definitions import Event

        dlq1 = []
        dlq2 = []

        def faulty_handler(event: Event):
            raise RuntimeError("fail")

        mock_bus.subscribe("chapter.created", faulty_handler)
        mock_bus.subscribe_dead_letter(dlq1.append)
        mock_bus.subscribe_dead_letter(dlq2.append)

        event = Event(
            event_type="chapter.created",
            timestamp=datetime.utcnow(),
            payload={},
        )
        mock_bus.publish(event)

        time.sleep(0.2)

        assert len(dlq1) == 1
        assert len(dlq2) == 1


# ============================================================
# T012-T014: 事件溯源
# ============================================================

class TestEventSourcing:
    """事件溯源日志测试"""

    def test_all_events_appended_to_log(self, mock_bus):
        """F00-T012: 所有发布事件追加到不可变日志"""
        from f00_kafka_eventbus.event_definitions import Event

        events_sent = []

        mock_bus.subscribe("chapter.created", lambda e: None)

        for i in range(5):
            event = Event(
                event_type="chapter.created",
                timestamp=datetime.utcnow(),
                payload={"index": i},
            )
            events_sent.append(event)
            mock_bus.publish(event)

        time.sleep(0.1)

        log = mock_bus.get_event_log()
        assert len(log) == 5

        for i, log_entry in enumerate(log):
            assert log_entry.event_type == "chapter.created"
            assert log_entry.payload["index"] == i

    def test_event_log_is_immutable(self, mock_bus):
        """F00-T012b: 事件日志不可直接修改"""
        from f00_kafka_eventbus.event_definitions import Event

        mock_bus.publish(Event(
            event_type="chapter.created",
            timestamp=datetime.utcnow(),
            payload={},
        ))

        time.sleep(0.1)

        log = mock_bus.get_event_log()

        with pytest.raises(Exception):
            log[0] = None  # 应不可修改

    def test_event_log_replay(self, mock_bus):
        """F00-T013: 可以重放事件日志"""
        from f00_kafka_eventbus.event_definitions import Event

        for i in range(3):
            mock_bus.publish(Event(
                event_type="chapter.created",
                timestamp=datetime.utcnow(),
                payload={"index": i},
            ))

        time.sleep(0.1)

        replayed = []
        mock_bus.replay_log(lambda e: replayed.append(e))

        assert len(replayed) == 3
        for i, event in enumerate(replayed):
            assert event.payload["index"] == i

    def test_event_log_preserved_after_shutdown(self, mock_bus):
        """F00-T013b: 日志在shutdown后仍然可读"""
        from f00_kafka_eventbus.event_definitions import Event

        mock_bus.subscribe("chapter.created", lambda e: None)

        for i in range(3):
            mock_bus.publish(Event(
                event_type="chapter.created",
                timestamp=datetime.utcnow(),
                payload={"index": i},
            ))

        time.sleep(0.1)

        log_before = mock_bus.get_event_log()
        mock_bus.shutdown()
        log_after = mock_bus.get_event_log()

        assert len(log_before) == 3
        assert len(log_after) == 3


# ============================================================
# T015-T017: 错误处理与重连
# ============================================================

class TestErrorHandling:
    """错误处理和重试测试"""

    def test_handler_error_does_not_crash_bus(self, mock_bus):
        """F00-T015: 处理器异常不影响总线和其他订阅者"""
        from f00_kafka_eventbus.event_definitions import Event

        normal_received = []

        def crashing_handler(event: Event):
            raise RuntimeError("crash")

        def normal_handler(event: Event):
            normal_received.append(event)

        mock_bus.subscribe("chapter.created", crashing_handler)
        mock_bus.subscribe("chapter.created", normal_handler)

        event = Event(
            event_type="chapter.created",
            timestamp=datetime.utcnow(),
            payload={},
        )
        mock_bus.publish(event)

        time.sleep(0.1)

        # 正常处理器仍应收到事件
        assert len(normal_received) == 1

    def test_at_least_once_semantics(self, mock_bus):
        """F00-T016: 至少一次语义 - 处理器确认机制"""
        from f00_kafka_eventbus.event_definitions import Event

        handled_events = []

        def handler_with_ack(event: Event):
            handled_events.append(event)

        mock_bus.subscribe("chapter.created", handler_with_ack)

        event = Event(
            event_type="chapter.created",
            timestamp=datetime.utcnow(),
            payload={"data": "test"},
        )
        mock_bus.publish(event)

        time.sleep(0.1)

        assert len(handled_events) == 1

    def test_retry_on_transient_failure(self, mock_bus):
        """F00-T016b: 瞬态失败自动重试"""
        from f00_kafka_eventbus.event_definitions import Event

        call_count = [0]
        received = []

        def retry_handler(event: Event):
            call_count[0] += 1
            if call_count[0] < 3:
                raise RuntimeError("transient error")
            received.append(event)

        mock_bus.subscribe(
            "chapter.created",
            retry_handler,
            max_retries=3,
            retry_delay=0.01,
        )

        event = Event(
            event_type="chapter.created",
            timestamp=datetime.utcnow(),
            payload={"data": "test"},
        )
        mock_bus.publish(event)

        time.sleep(0.5)

        assert len(received) == 1
        assert call_count[0] >= 2  # 至少重试了

    def test_max_retries_exceeded_goes_to_dlq(self, mock_bus):
        """F00-T016c: 超过最大重试次数进入死信队列"""
        from f00_kafka_eventbus.event_definitions import Event

        dlq_events = []

        def always_failing(event: Event):
            raise RuntimeError("always fail")

        def dlq_handler(event: Event):
            dlq_events.append(event)

        mock_bus.subscribe(
            "chapter.reviewed",
            always_failing,
            max_retries=2,
            retry_delay=0.01,
        )
        mock_bus.subscribe_dead_letter(dlq_handler)

        event = Event(
            event_type="chapter.reviewed",
            timestamp=datetime.utcnow(),
            payload={"data": "test"},
        )
        mock_bus.publish(event)

        time.sleep(0.3)

        assert len(dlq_events) == 1


# ============================================================
# T018-T020: 工厂模式与Kafka集成
# ============================================================

class TestEventBusFactory:
    """事件总线工厂测试"""

    def test_factory_creates_mock_bus_by_default(self):
        """F00-T018: 默认创建Mock事件总线"""
        from f00_kafka_eventbus.event_bus import create_event_bus

        bus = create_event_bus()
        assert bus is not None

        from f00_kafka_eventbus.mock_bus import MockEventBus
        assert isinstance(bus, MockEventBus)

        bus.shutdown()

    def test_factory_with_custom_config(self):
        """F00-T018b: 使用自定义配置创建总线"""
        from f00_kafka_eventbus.event_bus import create_event_bus

        config = {
            "bootstrap_servers": "custom:9092",
            "topic_prefix": "test",
        }
        bus = create_event_bus(config=config)

        from f00_kafka_eventbus.mock_bus import MockEventBus
        # 无Kafka时退化为Mock
        assert isinstance(bus, MockEventBus)

        bus.shutdown()

    def test_event_bus_shutdown_cleanup(self, mock_bus):
        """F00-T018c: shutdown后不能再发布事件"""
        from f00_kafka_eventbus.event_definitions import Event

        mock_bus.shutdown()

        # shutdown后发布应安全处理（不崩溃）
        event = Event(
            event_type="chapter.created",
            timestamp=datetime.utcnow(),
            payload={},
        )
        mock_bus.publish(event)

    def test_get_event_log_on_fresh_bus_is_empty(self, mock_bus):
        """F00-T019: 新总线的事件日志为空"""
        log = mock_bus.get_event_log()
        assert len(log) == 0

    def test_kafka_producer_config_available(self):
        """F00-T020: Kafka生产者配置可用"""
        from f00_kafka_eventbus.producer import KafkaConfig

        config = KafkaConfig(
            bootstrap_servers="localhost:9092",
            topic_prefix="textbook",
            consumer_group="textbook-system",
        )

        assert config.bootstrap_servers == "localhost:9092"
        assert config.topic_prefix == "textbook"
        assert config.consumer_group == "textbook-system"

    def test_kafka_producer_default_config(self):
        """F00-T020b: 默认Kafka配置"""
        from f00_kafka_eventbus.producer import KafkaConfig

        config = KafkaConfig()

        assert config.bootstrap_servers == "localhost:9092"
        assert config.topic_prefix == "textbook"
        assert config.consumer_group == "textbook-system"


# ============================================================
# T021-T023: 错误处理边界
# ============================================================

class TestErrorEdgeCases:
    """错误处理边界测试"""

    def test_subscribe_after_shutdown_raises(self, mock_bus):
        """F00-T021: shutdown后订阅抛出异常"""
        mock_bus.shutdown()

        with pytest.raises(RuntimeError):
            mock_bus.subscribe("chapter.created", lambda e: None)

    def test_replay_log_with_no_events(self, mock_bus):
        """F00-T022: 空日志重放"""
        replayed = []
        mock_bus.replay_log(lambda e: replayed.append(e))
        assert len(replayed) == 0

    def test_payload_with_large_data(self, mock_bus):
        """F00-T023: 大型payload正常处理"""
        from f00_kafka_eventbus.event_definitions import Event

        received = []

        mock_bus.subscribe("chapter.created", received.append)

        large_payload = {
            "content": "人工智能" * 10000,
            "metadata": {"key": f"value-{i}" for i in range(100)},
        }

        event = Event(
            event_type="chapter.created",
            timestamp=datetime.utcnow(),
            payload=large_payload,
        )
        mock_bus.publish(event)

        time.sleep(0.5)

        assert len(received) == 1
        assert received[0].payload["content"] == large_payload["content"]


# ============================================================
# T024-T026: 覆盖率补充
# ============================================================

class TestCoverageGaps:
    """补充覆盖率测试"""

    def test_event_equality(self):
        """F00-T024: 事件相等性基于event_id"""
        from f00_kafka_eventbus.event_definitions import Event

        e1 = Event(
            event_type="chapter.created",
            timestamp=datetime.utcnow(),
            payload={"data": "test"},
            event_id="same-id",
        )
        e2 = Event(
            event_type="chapter.reviewed",
            timestamp=datetime.utcnow(),
            payload={"data": "different"},
            event_id="same-id",
        )

        assert e1 == e2
        assert hash(e1) == hash(e2)

    def test_event_not_equal_different_id(self):
        """F00-T024b: 不同event_id不相等"""
        from f00_kafka_eventbus.event_definitions import Event

        e1 = Event(
            event_type="chapter.created",
            timestamp=datetime.utcnow(),
            payload={},
            event_id="id-1",
        )
        e2 = Event(
            event_type="chapter.created",
            timestamp=datetime.utcnow(),
            payload={},
            event_id="id-2",
        )

        assert e1 != e2

    def test_event_not_equal_non_event(self):
        """F00-T024c: Event与非Event对象不相等"""
        from f00_kafka_eventbus.event_definitions import Event

        e1 = Event(
            event_type="chapter.created",
            timestamp=datetime.utcnow(),
            payload={},
        )
        assert e1 != "not an event"
        assert e1 != None

    def test_event_repr(self):
        """F00-T024d: Event的repr格式"""
        from f00_kafka_eventbus.event_definitions import Event

        e1 = Event(
            event_type="chapter.created",
            timestamp=datetime.utcnow(),
            payload={},
            event_id="test-id",
        )
        r = repr(e1)
        assert "test-id" in r
        assert "chapter.created" in r

    def test_dlq_handler_exception_does_not_crash(self, mock_bus):
        """F00-T025: DLQ处理器自身异常不影响总线"""
        from f00_kafka_eventbus.event_definitions import Event

        def faulty_handler(event: Event):
            raise RuntimeError("original handler fails")

        def crashing_dlq(event: Event):
            raise RuntimeError("DLQ handler also fails")

        def good_dlq(event: Event):
            pass

        received = []
        mock_bus.subscribe("chapter.created", lambda e: received.append(e))
        mock_bus.subscribe("chapter.created", faulty_handler, max_retries=1, retry_delay=0.01)
        mock_bus.subscribe_dead_letter(crashing_dlq)
        mock_bus.subscribe_dead_letter(good_dlq)

        event = Event(
            event_type="chapter.created",
            timestamp=datetime.utcnow(),
            payload={"data": "test"},
        )
        mock_bus.publish(event)
        time.sleep(0.2)

        # 正常处理器不受影响
        assert len(received) >= 1

    def test_replay_log_handler_exception_does_not_crash(self, mock_bus):
        """F00-T025b: 重放时处理器异常不中断"""
        from f00_kafka_eventbus.event_definitions import Event

        mock_bus.publish(Event(
            event_type="chapter.created",
            timestamp=datetime.utcnow(),
            payload={"index": 0},
        ))
        mock_bus.publish(Event(
            event_type="chapter.created",
            timestamp=datetime.utcnow(),
            payload={"index": 1},
        ))

        time.sleep(0.1)

        replayed = []

        def crashing_handler(event: Event):
            if event.payload["index"] == 0:
                raise RuntimeError("replay crash")
            replayed.append(event)

        # 不应抛出异常
        mock_bus.replay_log(crashing_handler)

        # 第二个事件应被处理
        assert len(replayed) == 1

    def test_kafka_config_get_topic(self):
        """F00-T026: KafkaConfig.get_topic生成正确主题名"""
        from f00_kafka_eventbus.producer import KafkaConfig

        config = KafkaConfig(
            bootstrap_servers="localhost:9092",
            topic_prefix="textbook",
            consumer_group="textbook-system",
        )

        assert config.get_topic("chapter.created") == "textbook.chapter.created"
        assert config.get_topic("security.violation") == "textbook.security.violation"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
