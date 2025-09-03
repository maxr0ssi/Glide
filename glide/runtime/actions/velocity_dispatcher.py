"""Velocity-based scroll dispatcher."""

from __future__ import annotations

from typing import Optional

from glide.runtime.actions.config import ScrollConfig
from glide.runtime.actions.continuous_scroll import ContinuousScrollAction
from glide.gestures.velocity_tracker import Vec2D
from glide.gestures.velocity_controller import GestureState


class VelocityScrollDispatcher:
    """Dispatches velocity-based scroll events.
    
    Manages the lifecycle of scroll gestures using proper phases.
    """
    
    def __init__(self, config: ScrollConfig):
        """Initialize dispatcher.
        
        Args:
            config: Scroll configuration
        """
        self.config = config
        self.action = ContinuousScrollAction(config)
        self.last_state = GestureState.IDLE
        
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
            return True
            
        elif state == GestureState.IDLE and self.last_state == GestureState.SCROLLING:
            # Ending gesture
            self.action.end_gesture()
            self.last_state = state
            return True
            
        self.last_state = state
        return False