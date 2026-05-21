"""
F00: 事件定义模块

定义所有事件类型和Event数据结构。
"""

import json
import uuid
from datetime import datetime

# 预定义事件类型集合
EVENTS = {
    "chapter.created",
    "chapter.content_ready",
    "chapter.reviewed",
    "chapter.published",
    "security.violation",
    "quality.score_updated",
    "pipeline.stage_changed",
}


class InvalidEventTypeError(ValueError):
    """无效事件类型异常"""

    pass


class Event:
    """
    事件数据结构

    Attributes:
        event_id: 事件唯一标识 (UUID)
        event_type: 事件类型 (必须在EVENTS中)
        timestamp: UTC时间戳
        payload: 事件数据
    """

    def __init__(
        self,
        event_type: str,
        timestamp: datetime,
        payload: dict,
        event_id: str | None = None,
    ):
        if event_type not in EVENTS:
            raise InvalidEventTypeError(f"Invalid event type: {event_type}. " f"Must be one of: {sorted(EVENTS)}")

        self.event_type = event_type
        self.timestamp = timestamp
        self.payload = payload
        self.event_id = event_id or str(uuid.uuid4())

    def to_json(self) -> str:
        """序列化为JSON字符串"""
        return json.dumps(
            {
                "event_id": self.event_id,
                "event_type": self.event_type,
                "timestamp": self.timestamp.isoformat(),
                "payload": self.payload,
            },
            ensure_ascii=False,
        )

    @classmethod
    def from_json(cls, json_str: str) -> "Event":
        """从JSON字符串反序列化"""
        data = json.loads(json_str)
        return cls(
            event_id=data["event_id"],
            event_type=data["event_type"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            payload=data["payload"],
        )

    def __eq__(self, other):
        if not isinstance(other, Event):
            return False
        return self.event_id == other.event_id

    def __hash__(self):
        return hash(self.event_id)

    def __repr__(self):
        return f"Event(id={self.event_id}, type={self.event_type})"
