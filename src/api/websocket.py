"""
WebSocket Manager

Provides WebSocket connections for real-time updates.
"""

import json
import asyncio
from typing import Dict, Set, Callable, Any
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime


class ConnectionManager:
    """Manages WebSocket connections and message broadcasting."""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.message_handlers: Dict[str, Callable] = {}

    async def connect(self, websocket: WebSocket, channel: str = "global"):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = set()
        self.active_connections[channel].add(websocket)

    def disconnect(self, websocket: WebSocket, channel: str = "global"):
        """Remove a WebSocket connection."""
        if channel in self.active_connections:
            self.active_connections[channel].discard(websocket)
            if not self.active_connections[channel]:
                del self.active_connections[channel]

    async def send_message(self, message: dict, channel: str = "global"):
        """Send a message to all connections in a channel."""
        if channel not in self.active_connections:
            return
        message["timestamp"] = datetime.utcnow().isoformat()
        message_str = json.dumps(message, ensure_ascii=False)
        dead_connections = set()
        for connection in self.active_connections[channel]:
            try:
                await connection.send_text(message_str)
            except Exception:
                dead_connections.add(connection)
        for dead in dead_connections:
            self.disconnect(dead, channel)

    def register_handler(self, event_type: str, handler: Callable):
        """Register a handler for an event type."""
        self.message_handlers[event_type] = handler

    async def broadcast(self, event_type: str, data: Any, channel: str = "global"):
        """Broadcast an event to all connections in a channel."""
        message = {
            "type": event_type,
            "data": data,
        }
        await self.send_message(message, channel)


manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, channel: str = "global"):
    """WebSocket endpoint handler."""
    await manager.connect(websocket, channel)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                event_type = message.get("type")
                if event_type and event_type in manager.message_handlers:
                    result = await manager.message_handlers[event_type](message.get("data"))
                    await manager.send_message({
                        "type": f"{event_type}_response",
                        "data": result,
                    }, channel)
            except json.JSONDecodeError:
                await manager.send_message({
                    "type": "error",
                    "data": "Invalid JSON",
                }, channel)
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)