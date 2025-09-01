"""Circular and arc gesture detection for two-finger touch."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Deque, Optional, Tuple
from enum import Enum
import math
import time


class CircularDirection(Enum):
    CLOCKWISE = "CW"
    COUNTER_CLOCKWISE = "CCW"


@dataclass
class CircularEvent:
    """A circular gesture event."""
    ts_ms: int
    direction: CircularDirection
    total_angle_deg: float
    strength: float
    duration_ms: int
    
    def to_json_dict(self) -> dict:
        return {
            "ts_ms": self.ts_ms,
            "direction": self.direction.value,
            "total_angle_deg": self.total_angle_deg,
            "strength": self.strength,
            "duration_ms": self.duration_ms,
        }


@dataclass
class CircularDetection:
    """Result from circular detection."""
    event: Optional[CircularEvent]
    is_active: bool
    accumulated_angle: float


class CircularDetector:
    """Detects circular/arc motions when two fingers are touching."""
    
    def __init__(
        self,
        min_angle_deg: float = 90.0,
        max_angle_deg: float = 720.0,
        min_speed: float = 1.5,
        exit_speed_factor: float = 0.5,
        max_duration_ms: int = 1000,
        cooldown_ms: int = 500,
        angle_tolerance_deg: float = 45.0,
    ):
        self.min_angle_deg = min_angle_deg
        self.max_angle_deg = max_angle_deg
        self.min_speed = min_speed
        self.exit_speed = min_speed * exit_speed_factor
        self.max_duration_ms = max_duration_ms
        self.cooldown_ms = cooldown_ms
        self.angle_tolerance_deg = angle_tolerance_deg
        
        # State
        self._is_active = False
        self._start_time_ms = 0
        self._accumulated_angle = 0.0
        self._last_angle = None
        self._cooldown_until_ms = 0
        self._direction = None
        self._angle_changes = []
    
    def update(
        self,
        trail: Deque[Tuple[float, float]],
        finger_length: float,
        is_touching: bool,
        ts_now_ms: int,
    ) -> CircularDetection:
        """Update circular detection with current trail."""
        
        # Check cooldown
        if ts_now_ms < self._cooldown_until_ms:
            return CircularDetection(None, False, 0.0)
        
        # Reset if not touching
        if not is_touching:
            self._reset()
            return CircularDetection(None, False, 0.0)
        
        # Need at least 3 points for angle calculation
        if len(trail) < 3 or finger_length <= 1e-6:
            return CircularDetection(None, False, 0.0)
        
        # Calculate instantaneous speed
        p1 = trail[-2]
        p2 = trail[-1]
        dx = (p2[0] - p1[0]) / finger_length
        dy = (p2[1] - p1[1]) / finger_length
        speed = math.hypot(dx, dy) * 30.0  # Rough fps assumption
        
        # Calculate angle change
        if len(trail) >= 3:
            p0 = trail[-3]
            # Vectors
            v1 = (p1[0] - p0[0], p1[1] - p0[1])
            v2 = (p2[0] - p1[0], p2[1] - p1[1])
            
            # Skip if vectors too small
            if math.hypot(*v1) > 1e-6 and math.hypot(*v2) > 1e-6:
                # Cross product for signed angle
                cross = v1[0] * v2[1] - v1[1] * v2[0]
                dot = v1[0] * v2[0] + v1[1] * v2[1]
                angle_rad = math.atan2(cross, dot)
                angle_deg = math.degrees(angle_rad)
                
                # Start detection
                if not self._is_active and speed >= self.min_speed:
                    self._start(ts_now_ms, angle_deg)
                
                # Continue detection
                elif self._is_active:
                    # Check timeout
                    if ts_now_ms - self._start_time_ms > self.max_duration_ms:
                        return self._stop(ts_now_ms, "timeout")
                    
                    # Check speed
                    if speed < self.exit_speed:
                        return self._stop(ts_now_ms, "slow")
                    
                    # Accumulate angle if consistent direction
                    if self._is_consistent_direction(angle_deg):
                        self._accumulated_angle += angle_deg
                        self._angle_changes.append(angle_deg)
                        
                        # Check if we've accumulated enough
                        abs_angle = abs(self._accumulated_angle)
                        if abs_angle >= self.min_angle_deg:
                            # Success!
                            return self._complete(ts_now_ms)
                        
                        # Check max angle
                        if abs_angle > self.max_angle_deg:
                            return self._stop(ts_now_ms, "too_far")
        
        return CircularDetection(None, self._is_active, self._accumulated_angle)
    
    def _start(self, ts_ms: int, initial_angle: float):
        """Start tracking a circular motion."""
        self._is_active = True
        self._start_time_ms = ts_ms
        self._accumulated_angle = initial_angle
        self._angle_changes = [initial_angle]
        self._direction = CircularDirection.CLOCKWISE if initial_angle > 0 else CircularDirection.COUNTER_CLOCKWISE
    
    def _is_consistent_direction(self, angle_deg: float) -> bool:
        """Check if angle change is consistent with current direction."""
        if self._direction == CircularDirection.CLOCKWISE:
            return angle_deg > -self.angle_tolerance_deg
        else:
            return angle_deg < self.angle_tolerance_deg
    
    def _complete(self, ts_ms: int) -> CircularDetection:
        """Complete a successful circular gesture."""
        duration_ms = ts_ms - self._start_time_ms
        total_angle = abs(self._accumulated_angle)
        
        # Calculate strength based on angle completed and consistency
        angle_score = min(1.0, total_angle / 180.0)
        consistency_score = self._calculate_consistency()
        strength = 0.7 * angle_score + 0.3 * consistency_score
        
        event = CircularEvent(
            ts_ms=ts_ms,
            direction=self._direction,
            total_angle_deg=total_angle,
            strength=strength,
            duration_ms=duration_ms,
        )
        
        self._reset()
        self._cooldown_until_ms = ts_ms + self.cooldown_ms
        
        return CircularDetection(event, False, 0.0)
    
    def _stop(self, ts_ms: int, reason: str) -> CircularDetection:
        """Stop tracking without emitting event."""
        self._reset()
        return CircularDetection(None, False, 0.0)
    
    def _reset(self):
        """Reset detector state."""
        self._is_active = False
        self._start_time_ms = 0
        self._accumulated_angle = 0.0
        self._angle_changes = []
        self._direction = None
    
    def _calculate_consistency(self) -> float:
        """Calculate how consistent the rotation was."""
        if not self._angle_changes:
            return 0.0
        
        # Count how many angle changes were in the right direction
        if self._direction == CircularDirection.CLOCKWISE:
            consistent = sum(1 for a in self._angle_changes if a > 0)
        else:
            consistent = sum(1 for a in self._angle_changes if a < 0)
        
        return consistent / len(self._angle_changes)