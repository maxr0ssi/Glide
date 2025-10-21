"""Simplified velocity-based scroll controller."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from glide.gestures.velocity_tracker import Vec2D


class GestureState(Enum):
    """Simple gesture states."""

    IDLE = "idle"
    SCROLLING = "scrolling"


@dataclass
class VelocityUpdate:
    """Velocity update from controller."""

    velocity: Vec2D
    state: GestureState
    is_active: bool


class VelocityController:
    """Controls scroll gestures based on velocity.

    Much simpler than WheelController - just tracks touch state
    and passes velocity through. macOS handles all the complexity.
    """

    def __init__(self, min_velocity: float = 0.001):
        """Initialize controller.

        Args:
            min_velocity: Minimum velocity magnitude to start scrolling
        """
        self.min_velocity = min_velocity
        self.state = GestureState.IDLE
        self.was_touching = False

    def update(
        self, velocity: Vec2D | None, is_touching: bool, is_high_five: bool, timestamp_ms: int
    ) -> VelocityUpdate:
        """Update controller state.

        Args:
            velocity: Current velocity from tracker
            is_touching: Whether fingers are touching
            is_high_five: High-five gesture stops scrolling
            timestamp_ms: Current timestamp

        Returns:
            Velocity update with state
        """
        # High-five always stops
        if is_high_five:
            self.state = GestureState.IDLE
            return VelocityUpdate(velocity=Vec2D(0, 0), state=self.state, is_active=False)

        # Handle state transitions
        if self.state == GestureState.IDLE:
            # Start scrolling when touching with velocity
            if is_touching and velocity and velocity.magnitude > self.min_velocity:
                self.state = GestureState.SCROLLING

        elif self.state == GestureState.SCROLLING:
            # Stop when fingers lift
            if not is_touching and self.was_touching:
                # Let the scroll action know to end the gesture
                # macOS will handle momentum
                self.state = GestureState.IDLE

        self.was_touching = is_touching

        # Return current state
        return VelocityUpdate(
            velocity=velocity or Vec2D(0, 0),
            state=self.state,
            is_active=(self.state == GestureState.SCROLLING and is_touching),
        )
