"""Velocity-based scroll dispatcher."""

from __future__ import annotations

from typing import Optional

from glide.runtime.actions.config import ScrollConfig
from glide.runtime.actions.continuous_scroll import ContinuousScrollAction
from glide.gestures.velocity_tracker import Vec2D
from glide.gestures.velocity_controller import GestureState
from glide.runtime.ipc.ws import WebSocketBroadcaster


class VelocityScrollDispatcher:
    """Dispatches velocity-based scroll events.
    
    Manages the lifecycle of scroll gestures using proper phases.
    """
    
    def __init__(self, config: ScrollConfig, ws_broadcaster: Optional[WebSocketBroadcaster] = None):
        """Initialize dispatcher.
        
        Args:
            config: Scroll configuration
            ws_broadcaster: Optional WebSocket broadcaster for HUD events
        """
        self.config = config
        self.action = ContinuousScrollAction(config)
        self.last_state = GestureState.IDLE
        self.ws_broadcaster = ws_broadcaster
        
    def dispatch(
        self,
        velocity: Vec2D,
        state: GestureState,
        is_active: bool
    ) -> bool:
        """Dispatch scroll based on velocity and state.
        
        Args:
            velocity: Current velocity vector
            state: Current gesture state
            is_active: Whether gesture is active
            
        Returns:
            True if scroll was dispatched
        """
        # Handle state transitions
        if state == GestureState.SCROLLING and self.last_state == GestureState.IDLE:
            # Starting a new gesture
            self.action.begin_gesture(velocity)
            self.last_state = state
            return True
            
        elif state == GestureState.SCROLLING and is_active:
            # Continuing gesture
            self.action.update_gesture(velocity)
            
            # Broadcast to WebSocket clients
            if self.ws_broadcaster:
                # Calculate normalized speed (0-1)
                speed_normalized = min(abs(velocity.y) / self.config.max_velocity, 1.0)
                self.ws_broadcaster.publish_scroll(velocity.y, speed_normalized)
            
            return True
            
        elif state == GestureState.IDLE and self.last_state == GestureState.SCROLLING:
            # Ending gesture
            self.action.end_gesture()
            
            # Send hide event
            if self.ws_broadcaster:
                self.ws_broadcaster.publish_hide()
            
            self.last_state = state
            return True
            
        self.last_state = state
        return False