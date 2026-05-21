"""
WebSocket Manager

Provides WebSocket connections for real-time updates.
"""

import json
from collections.abc import Callable
from datetime import datetime
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    """Manages WebSocket connections and message broadcasting."""

    def __init__(self):
        self.active_connections: dict[str, set[WebSocket]] = {}
        self.message_handlers: dict[str, Callable] = {}

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
    """WebSocket endpoint handler with JWT authentication."""
    # API-SEC-007: Validate channel parameter
    if not channel or not isinstance(channel, str):
        await websocket.close(code=4000, reason="Invalid channel")
        return
    if len(channel) > 50 or not channel.replace("_", "").replace("-", "").isalnum():
        await websocket.close(code=4000, reason="Invalid channel format")
        return

    # API-SEC-002: Verify JWT token from query param
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Authentication required")
        return

    try:
        from api.deps import decode_token
        token_data = decode_token(token, "access")
        # Optionally store user info in websocket state
        websocket.state.user_id = token_data.sub
        websocket.state.user_role = token_data.role
    except Exception:
        await websocket.close(code=4002, reason="Invalid or expired token")
        return

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
