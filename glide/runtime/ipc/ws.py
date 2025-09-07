"""WebSocket broadcaster for HUD events.

Implements a local-only WebSocket server that broadcasts scroll events
to connected HUD clients. Includes throttling and session token support.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import secrets
import threading
import time

import numpy as np
import websockets.server
import websockets.typing

try:
    import cv2
except ImportError:
    cv2 = None  # Handle gracefully if OpenCV not available

try:
    import websockets
    import websockets.exceptions
    import websockets.server
except ImportError:
    raise ImportError("websockets library required. Install with: pip install websockets>=12.0")


logger = logging.getLogger(__name__)


class ThrottleController:
    """Rate limiter for WebSocket events."""

    def __init__(self, rate_hz: int):
        """Initialize with target rate in Hz."""
        self.min_interval = 1.0 / rate_hz
        self.last_sent = 0.0

    def should_send(self) -> bool:
        """Check if enough time has passed to send next event."""
        now = time.time()
        if now - self.last_sent >= self.min_interval:
            self.last_sent = now
            return True
        return False

    def reset(self) -> None:
        """Reset throttle timer."""
        self.last_sent = 0.0


class WebSocketBroadcaster:
    """Local-only WebSocket broadcaster for HUD events.

    Broadcasts scroll events to connected clients with throttling
    and optional session token authentication.
    """

    def __init__(
        self,
        port: int = 8765,
        session_token: str | None = None,
        throttle_hz: int = 60,
        camera_throttle_hz: int = 60,
    ):
        """Initialize WebSocket broadcaster.

        Args:
            port: Port to listen on (localhost only)
            session_token: Optional security token (auto-generated if None)
            throttle_hz: Maximum event rate in Hz for scroll events
            camera_throttle_hz: Maximum frame rate for camera streaming
        """
        self.port = port
        self.session_token = session_token or secrets.token_urlsafe(16)
        self.throttle = ThrottleController(throttle_hz)
        self.camera_throttle = ThrottleController(camera_throttle_hz)
        self.clients: set[websockets.server.WebSocketServerProtocol] = set()
        self.expanded_mode_clients: set[websockets.server.WebSocketServerProtocol] = set()
        self.camera_enabled_clients: set[websockets.server.WebSocketServerProtocol] = set()

        # Asyncio components
        self.loop: asyncio.AbstractEventLoop | None = None
        self.server = None
        self.thread: threading.Thread | None = None
        self._running = False

        # Start server in background thread
        self._start_server()

    def _start_server(self) -> None:
        """Start WebSocket server in background thread."""
        self.thread = threading.Thread(target=self._run_server, daemon=True)
        self.thread.start()

        # Wait for server to start
        timeout = 5.0
        start_time = time.time()
        while not self._running and (time.time() - start_time) < timeout:
            time.sleep(0.1)

        if not self._running:
            raise RuntimeError("Failed to start WebSocket server")

    def _run_server(self) -> None:
        """Run asyncio event loop in thread."""
        try:
            # Create new event loop for this thread
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

            # Run the server setup in the event loop
            self.loop.run_until_complete(self._start_server_async())

            # Run event loop
            self.loop.run_forever()

        except (OSError, RuntimeError) as e:
            logger.error(f"WebSocket server error: {e}")
            import traceback

            traceback.print_exc()
        finally:
            self._running = False
            if self.loop and not self.loop.is_closed():
                self.loop.close()

    async def _start_server_async(self) -> None:
        """Start the WebSocket server asynchronously."""
        # Create and start the server
        self.server = await websockets.serve(
            self._handler, "127.0.0.1", self.port  # Localhost only
        )
        self._running = True
        logger.info(f"WebSocket server started on ws://127.0.0.1:{self.port}/hud")

    async def _handler(self, websocket: websockets.server.WebSocketServerProtocol) -> None:
        """Handle WebSocket connections."""
        # Register client
        self.clients.add(websocket)
        logger.info("Client connected")

        try:
            # Send initial config
            await self._send_config(websocket)

            # Listen for messages from client
            async for message in websocket:
                await self._handle_client_message(websocket, message)

        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients.remove(websocket)
            self.expanded_mode_clients.discard(websocket)
            self.camera_enabled_clients.discard(websocket)
            logger.info("Client disconnected")

    async def _send_config(self, websocket: websockets.server.WebSocketServerProtocol) -> None:
        """Send initial configuration to client."""
        config_msg = json.dumps({"type": "config", "position": "bottom-right", "opacity": 0.85})
        await websocket.send(config_msg)

    async def _handle_client_message(
        self, websocket: websockets.server.WebSocketServerProtocol, message: str
    ) -> None:
        """Handle messages from client."""
        try:
            data = json.loads(message)
            msg_type = data.get("type")

            if msg_type == "mode":
                expanded = data.get("expanded", False)
                if expanded:
                    self.expanded_mode_clients.add(websocket)
                    logger.info("Client switched to expanded mode - camera streaming enabled")
                else:
                    self.expanded_mode_clients.discard(websocket)
                    logger.info("Client switched to minimized mode - camera streaming disabled")
            elif msg_type == "camera_enabled":
                enabled = data.get("enabled", True)
                if enabled:
                    self.camera_enabled_clients.add(websocket)
                    logger.info("Client enabled camera streaming")
                else:
                    self.camera_enabled_clients.discard(websocket)
                    logger.info("Client disabled camera streaming")

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON from client: {message}")
        except (KeyError, AttributeError, ValueError) as e:
            logger.error(f"Error handling client message: {e}")

    def publish_scroll(self, vy: float, speed_0_1: float) -> None:
        """Publish scroll event to all clients.

        Args:
            vy: Vertical scroll velocity
            speed_0_1: Normalized speed (0-1)
        """
        if not self.clients:
            logger.debug("No clients connected to send scroll event")
            return

        if not self.throttle.should_send():
            return

        message = json.dumps(
            {
                "type": "scroll",
                "vy": round(vy, 2),
                "speed": round(min(max(speed_0_1, 0.0), 1.0), 2),  # Clamp to 0-1
            }
        )

        # logger.debug(f"Broadcasting scroll event: {message}")
        self._broadcast(message)

    def publish_hide(self) -> None:
        """Publish hide event to all clients."""
        if not self.clients:
            return

        message = json.dumps({"type": "hide"})
        self._broadcast(message)
        self.throttle.reset()

    def publish_touchproof(self, active: bool, hands_count: int) -> None:
        """Publish TouchProof state to all clients.

        Args:
            active: Whether TouchProof is currently active
            hands_count: Number of hands detected
        """
        if not self.clients:
            return

        message = json.dumps({"type": "touchproof", "active": active, "hands": hands_count})

        logger.debug(f"Broadcasting touchproof event: {message}")
        self._broadcast(message)

    def publish_camera_frame(
        self, frame_bgr: np.ndarray, target_width: int = 320, jpeg_quality: int = 60
    ) -> None:
        """Publish camera frame to clients in expanded mode.

        Args:
            frame_bgr: OpenCV BGR frame
            target_width: Target width for resize (maintains aspect ratio)
            jpeg_quality: JPEG compression quality (1-100)
        """
        # Only send to clients in expanded mode
        if not self.expanded_mode_clients or cv2 is None:
            return

        if not self.camera_throttle.should_send():
            return

        try:
            # Resize frame to target width maintaining aspect ratio
            height, width = frame_bgr.shape[:2]
            target_height = int(height * target_width / width)
            resized = cv2.resize(frame_bgr, (target_width, target_height))

            # Encode as JPEG (imencode expects BGR format)
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality]
            _, buffer = cv2.imencode(".jpg", resized, encode_params)

            # Base64 encode
            frame_base64 = base64.b64encode(buffer).decode("utf-8")

            message = json.dumps(
                {
                    "type": "camera",
                    "frame": frame_base64,
                    "width": target_width,
                    "height": target_height,
                }
            )

            # Only broadcast to expanded mode clients
            self._broadcast_to_clients(message, self.expanded_mode_clients)

        except (cv2.error, ValueError, MemoryError) as e:
            logger.error(f"Error publishing camera frame: {e}")

    def _broadcast(self, message: str) -> None:
        """Broadcast message to all connected clients."""
        if not self.loop or not self._running:
            return

        # Schedule coroutine in the server's event loop
        asyncio.run_coroutine_threadsafe(self._async_broadcast(message), self.loop)

    async def _async_broadcast(self, message: str) -> None:
        """Async broadcast implementation."""
        if not self.clients:
            return

        # Send to all clients concurrently
        disconnected = []

        async def send_to_client(client: websockets.server.WebSocketServerProtocol) -> None:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected.append(client)

        # Send to all clients
        await asyncio.gather(
            *[send_to_client(client) for client in self.clients], return_exceptions=True
        )

        # Remove disconnected clients
        for client in disconnected:
            self.clients.discard(client)
            self.expanded_mode_clients.discard(client)
            self.camera_enabled_clients.discard(client)

    def _broadcast_to_clients(self, message: str, clients: set) -> None:
        """Broadcast message to specific set of clients."""
        if not self.loop or not self._running or not clients:
            return

        # Schedule coroutine in the server's event loop
        asyncio.run_coroutine_threadsafe(
            self._async_broadcast_to_clients(message, clients), self.loop
        )

    async def _async_broadcast_to_clients(self, message: str, clients: set) -> None:
        """Async broadcast to specific clients."""
        if not clients:
            return

        # Send to specified clients concurrently
        disconnected = []

        async def send_to_client(client: websockets.server.WebSocketServerProtocol) -> None:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected.append(client)

        # Send to specified clients
        await asyncio.gather(
            *[send_to_client(client) for client in clients], return_exceptions=True
        )

        # Remove disconnected clients
        for client in disconnected:
            self.clients.discard(client)
            self.expanded_mode_clients.discard(client)
            self.camera_enabled_clients.discard(client)

    def stop(self) -> None:
        """Stop WebSocket server."""
        logger.info("Stopping WebSocket server...")

        if self.server and self.loop and not self.loop.is_closed():  # type: ignore[unreachable]
            # Schedule server close in the event loop  # type: ignore[unreachable]
            future = asyncio.run_coroutine_threadsafe(self._async_close_server(), self.loop)  # type: ignore[unreachable]

            # Wait for close to complete
            try:
                future.result(timeout=2.0)
            except (asyncio.TimeoutError, RuntimeError) as e:
                logger.warning(f"Error closing server: {e}")

            # Stop event loop
            self.loop.call_soon_threadsafe(self.loop.stop)

        # Wait for thread to finish
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)

        self._running = False
        logger.info("WebSocket server stopped")

    async def _async_close_server(self) -> None:
        """Async helper to close the server."""
        if self.server:
            self.server.close()  # type: ignore[unreachable]
            await self.server.wait_closed()
