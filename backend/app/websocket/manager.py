"""
WebSocket Connection Manager for QDS SIEM.

Manages real-time connections from dashboard clients.
Broadcasts new events and threats as they are detected.
"""

import json
import logging
from typing import List, Dict, Any
from fastapi import WebSocket

logger = logging.getLogger("qds.websocket")


class ConnectionManager:
    """Manage WebSocket connections for real-time dashboard updates."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        """Send message to all connected clients."""
        if not self.active_connections:
            return

        data = json.dumps(message, default=str)
        disconnected = []

        for connection in self.active_connections:
            try:
                await connection.send_text(data)
            except Exception:
                disconnected.append(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

    async def send_personal(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send message to a specific client."""
        try:
            await websocket.send_text(json.dumps(message, default=str))
        except Exception:
            self.disconnect(websocket)

    @property
    def connection_count(self) -> int:
        return len(self.active_connections)


# Singleton instance
ws_manager = ConnectionManager()
