"""Velocity tracking for smooth scrolling gestures."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass


@dataclass
class Vec2D:
    """2D velocity vector."""

    x: float
    y: float

    @property
    def magnitude(self) -> float:
        """Get velocity magnitude."""
        return float((self.x**2 + self.y**2) ** 0.5)


@dataclass
class PositionSample:
    """Single position sample with timestamp."""

    x: float
    y: float
    timestamp_ms: int


class VelocityTracker:
    """Tracks fingertip velocity for smooth scrolling.

    Instead of calculating angles, this directly tracks velocity
    in pixels per second, providing a more natural scrolling experience.
    """

    def __init__(self, window_ms: int = 100, smoothing_factor: float = 0.3):
        """Initialize velocity tracker.

        Args:
            window_ms: Time window for velocity calculation (default 100ms)
            smoothing_factor: EMA smoothing factor (0-1, higher = more responsive)
        """
        self.window_ms = window_ms
        self.smoothing_factor = smoothing_factor
        self.samples: deque[PositionSample] = deque()
        self.last_velocity: Vec2D | None = None
        self.min_samples = 2  # Minimum samples for velocity calculation
        self.noise_threshold = 0.5  # Pixels - ignore tiny movements

    def update(
        self,
        index_tip: tuple[float, float],
        middle_tip: tuple[float, float],
        is_touching: bool,
        timestamp_ms: int,
    ) -> Vec2D | None:
        """Calculate velocity from fingertip positions.

        Args:
            index_tip: (x, y) position of index fingertip (0-1 normalized)
            middle_tip: (x, y) position of middle fingertip (0-1 normalized)
            is_touching: Whether fingers are in contact
            timestamp_ms: Current timestamp

        Returns:
            Velocity vector in pixels/second, or None if invalid
        """
        # Reset on touch end
        if not is_touching:
            self.reset()
            return None

        # Calculate midpoint between fingertips
        mid_x = (index_tip[0] + middle_tip[0]) / 2
        mid_y = (index_tip[1] + middle_tip[1]) / 2

        # Add new sample
        self.samples.append(PositionSample(mid_x, mid_y, timestamp_ms))

        # Remove old samples outside window
        cutoff_time = timestamp_ms - self.window_ms
        while self.samples and self.samples[0].timestamp_ms < cutoff_time:
            self.samples.popleft()

        # Need at least 2 samples for velocity
        if len(self.samples) < self.min_samples:
            return None

        # Calculate weighted average velocity
        velocity = self._calculate_velocity()

        # Apply smoothing if we have previous velocity
        if self.last_velocity and velocity:
            velocity.x = (
                self.smoothing_factor * velocity.x
                + (1 - self.smoothing_factor) * self.last_velocity.x
            )
            velocity.y = (
                self.smoothing_factor * velocity.y
                + (1 - self.smoothing_factor) * self.last_velocity.y
            )

        self.last_velocity = velocity
        return velocity

    def _calculate_velocity(self) -> Vec2D | None:
        """Calculate velocity from position samples."""
        if len(self.samples) < 2:
            return None

        # Use simple difference between first and last samples
        # For more samples, could use weighted average
        first = self.samples[0]
        last = self.samples[-1]

        dt_ms = last.timestamp_ms - first.timestamp_ms
        if dt_ms <= 0:
            return None

        # Calculate velocity in normalized units per second
        # Note: These are normalized coordinates (0-1), need to scale to pixels
        vx = (last.x - first.x) * 1000 / dt_ms
        vy = (last.y - first.y) * 1000 / dt_ms

        # Apply noise threshold
        if abs(vx) < self.noise_threshold / 1000:
            vx = 0
        if abs(vy) < self.noise_threshold / 1000:
            vy = 0

        return Vec2D(vx, vy)

    def reset(self) -> None:
        """Reset tracker state."""
        self.samples.clear()
        self.last_velocity = None
