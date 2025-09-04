"""WebSocket broadcaster for HUD events (Phase 2).

TODO: Implement in Phase 2
- Local-only WebSocket broadcaster
- API: publish_scroll(vy: float, speed_0_1: float), publish_hide()
- Throttle to 30-60 Hz, drop when no clients
- Optional random session token
"""

from __future__ import annotations


class WebSocketBroadcaster:
    """Placeholder for WebSocket HUD event broadcaster.
    
    Will broadcast scroll events to connected HUD clients.
    To be implemented in Phase 2.
    """
    
    def __init__(self, port: int = 8765):
        """Initialize broadcaster (placeholder)."""
        self.port = port
        # TODO: Phase 2 implementation
        
    def publish_scroll(self, vy: float, speed_0_1: float) -> None:
        """Publish scroll event (placeholder)."""
        # TODO: Phase 2 - broadcast {"type":"scroll","vy":vy,"speed":speed_0_1}
        pass
        
    def publish_hide(self) -> None:
        """Publish hide event (placeholder)."""
        # TODO: Phase 2 - broadcast {"type":"hide"}
        pass