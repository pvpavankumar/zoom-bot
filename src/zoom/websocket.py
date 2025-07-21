
import asyncio
import json
from typing import Dict, Optional, Callable, Any
import websockets

from ..core.config import settings
from ..utils.logging import get_logger

logger = get_logger(__name__)


class ZoomWebSocketManager:

    def __init__(self):
        self.connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.event_handlers: Dict[str, Callable] = {}
        self.is_running = False

    async def start(self, host: str = "localhost", port: int = 8765):
        try:
            self.server = await websockets.serve(
                self._handle_connection,
                host,
                port
            )
            self.is_running = True
            logger.info(f"WebSocket server started on {host}:{port}")

        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {e}")
            raise

    async def stop(self):
        if hasattr(self, 'server'):
            self.server.close()
            await self.server.wait_closed()

        self.is_running = False
        self.connections.clear()
        logger.info("WebSocket server stopped")

    def register_event_handler(self, event_type: str, handler: Callable):
        self.event_handlers[event_type] = handler
        logger.debug(f"Registered handler for event type: {event_type}")

    async def broadcast_event(self, event_type: str, data: Dict[str, Any]):
        if not self.connections:
            return

        message = json.dumps({
            "type": event_type,
            "data": data,
            "timestamp": asyncio.get_event_loop().time()
        })

        disconnected = []
        for connection_id, websocket in self.connections.items():
            try:
                await websocket.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected.append(connection_id)
            except Exception as e:
                logger.error(f"Error sending message to {connection_id}: {e}")
                disconnected.append(connection_id)

        for connection_id in disconnected:
            del self.connections[connection_id]

    async def send_to_connection(self, connection_id: str, event_type: str, data: Dict[str, Any]):
        if connection_id not in self.connections:
            logger.warning(f"Connection {connection_id} not found")
            return

        message = json.dumps({
            "type": event_type,
            "data": data,
            "timestamp": asyncio.get_event_loop().time()
        })

        try:
            await self.connections[connection_id].send(message)
        except Exception as e:
            logger.error(f"Error sending message to {connection_id}: {e}")
            del self.connections[connection_id]

    async def _handle_connection(self, websocket, path):
        connection_id = f"conn_{len(self.connections)}"
        self.connections[connection_id] = websocket

        logger.info(f"New WebSocket connection: {connection_id}")

        try:
            await websocket.send(json.dumps({
                "type": "connection_established",
                "connection_id": connection_id,
                "message": "Connected to Zoom Interview Bot"
            }))

            async for message in websocket:
                await self._handle_message(connection_id, message)

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"WebSocket connection closed: {connection_id}")
        except Exception as e:
            logger.error(f"Error in WebSocket connection {connection_id}: {e}")
        finally:
            if connection_id in self.connections:
                del self.connections[connection_id]

    async def _handle_message(self, connection_id: str, message: str):
        try:
            data = json.loads(message)
            event_type = data.get("type")

            if not event_type:
                logger.warning(f"Message without event type from {connection_id}")
                return

            if event_type in self.event_handlers:
                await self.event_handlers[event_type](connection_id, data)
            else:
                logger.debug(f"No handler for event type: {event_type}")

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON from {connection_id}: {message}")
        except Exception as e:
            logger.error(f"Error handling message from {connection_id}: {e}")


websocket_manager = ZoomWebSocketManager()
