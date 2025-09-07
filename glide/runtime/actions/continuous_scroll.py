"""Continuous scroll implementation using macOS scroll phases."""

from __future__ import annotations

import platform
from typing import Any

if platform.system() != "Darwin":
    raise ImportError("ContinuousScrollAction is only available on macOS")

try:
    from AppKit import NSUserDefaults
    from Quartz import (
        CGEventCreateScrollWheelEvent,
        CGEventPost,
        CGEventSetDoubleValueField,
        CGEventSetIntegerValueField,
        kCGHIDEventTap,
        kCGMomentumScrollPhaseNone,
        kCGScrollEventUnitPixel,
        kCGScrollPhaseBegan,
        kCGScrollPhaseChanged,
        kCGScrollPhaseEnded,
        kCGScrollWheelEventIsContinuous,
        kCGScrollWheelEventMomentumPhase,
        kCGScrollWheelEventPointDeltaAxis1,
        kCGScrollWheelEventPointDeltaAxis2,
        kCGScrollWheelEventScrollPhase,
    )
except ImportError as e:
    raise ImportError(f"PyObjC is required for ContinuousScrollAction: {e}")

from glide.gestures.velocity_tracker import Vec2D
from glide.runtime.actions.config import ScrollConfig


class ContinuousScrollAction:
    """Native macOS continuous scroll implementation.

    Uses proper scroll phases for smooth, native-feeling scrolling
    that integrates with macOS momentum and acceleration.
    """

    def __init__(self, config: ScrollConfig):
        """Initialize with configuration."""
        self.config = config
        self.is_scrolling = False
        self.natural_scrolling = self._detect_natural_scrolling()

        # Scale factor to convert normalized velocity to pixels
        # Assuming 1920x1080 screen, adjust as needed
        self.screen_height = 1080
        self.velocity_scale = 500.0  # Tune this for responsiveness

    def begin_gesture(self, velocity: Vec2D) -> bool:
        """Begin a new scroll gesture.

        Args:
            velocity: Initial velocity vector

        Returns:
            True if gesture began successfully
        """
        if self.is_scrolling:
            return False

        # Convert velocity to pixels
        delta_x, delta_y = self._velocity_to_pixels(velocity)

        # Create scroll event with began phase
        event = self._create_phase_event(delta_x, delta_y, kCGScrollPhaseBegan)
        if event:
            CGEventPost(kCGHIDEventTap, event)
            self.is_scrolling = True
            # print(f"[SCROLL] Began gesture: dx={delta_x:.1f}, dy={delta_y:.1f}")
            return True

        return False

    def update_gesture(self, velocity: Vec2D) -> bool:
        """Update ongoing scroll gesture.

        Args:
            velocity: Current velocity vector

        Returns:
            True if update was successful
        """
        if not self.is_scrolling:
            # Auto-begin if needed
            return self.begin_gesture(velocity)

        # Convert velocity to pixels
        delta_x, delta_y = self._velocity_to_pixels(velocity)

        # Skip tiny movements
        if abs(delta_x) < 0.1 and abs(delta_y) < 0.1:
            return True

        # Create scroll event with changed phase
        event = self._create_phase_event(delta_x, delta_y, kCGScrollPhaseChanged)
        if event:
            CGEventPost(kCGHIDEventTap, event)
            return True

        return False

    def end_gesture(self) -> bool:
        """End the current scroll gesture.

        macOS will automatically handle momentum scrolling.

        Returns:
            True if gesture ended successfully
        """
        if not self.is_scrolling:
            return False

        # Create scroll event with ended phase
        # Use zero deltas for the end event
        event = self._create_phase_event(0.0, 0.0, kCGScrollPhaseEnded)
        if event:
            CGEventPost(kCGHIDEventTap, event)
            self.is_scrolling = False
            # print(f"[SCROLL] Ended gesture - momentum handoff to macOS")
            return True

        return False

    def _create_phase_event(self, delta_x: float, delta_y: float, phase: int) -> Any:
        """Create a scroll event with proper phase."""
        try:
            # Create base scroll event using CGEventCreateScrollWheelEvent
            # Note: We use the regular version since CGEventCreateScrollWheelEvent2 may not be available
            event = CGEventCreateScrollWheelEvent(
                None,  # source
                kCGScrollEventUnitPixel,  # units
                2,  # wheelCount
                int(delta_y),  # wheel1 (vertical) - integer part
                int(delta_x),  # wheel2 (horizontal) - integer part
            )

            if not event:
                return None

            # Mark as continuous gesture
            CGEventSetIntegerValueField(event, kCGScrollWheelEventIsContinuous, 1)

            # Set scroll phase
            CGEventSetIntegerValueField(event, kCGScrollWheelEventScrollPhase, phase)

            # Set momentum phase to none (we're in gesture phase)
            CGEventSetIntegerValueField(
                event, kCGScrollWheelEventMomentumPhase, kCGMomentumScrollPhaseNone
            )

            # Set fractional pixel deltas for smooth scrolling
            # These provide sub-pixel precision
            CGEventSetDoubleValueField(event, kCGScrollWheelEventPointDeltaAxis1, delta_y)
            CGEventSetDoubleValueField(event, kCGScrollWheelEventPointDeltaAxis2, delta_x)

            return event

        except Exception:
            # print(f"[SCROLL ERROR] Failed to create event: {e}")
            return None

    def _velocity_to_pixels(self, velocity: Vec2D) -> tuple[float, float]:
        """Convert normalized velocity to pixel deltas."""
        # Scale normalized velocity to pixels
        pixel_vx = velocity.x * self.velocity_scale
        pixel_vy = velocity.y * self.velocity_scale

        # Apply natural scrolling if enabled
        if self.natural_scrolling:
            pixel_vy = -pixel_vy

        # Apply max velocity clamping
        max_vel = self.config.max_velocity
        if abs(pixel_vy) > max_vel:
            pixel_vy = max_vel if pixel_vy > 0 else -max_vel
        if abs(pixel_vx) > max_vel:
            pixel_vx = max_vel if pixel_vx > 0 else -max_vel

        return (pixel_vx, pixel_vy)

    def _detect_natural_scrolling(self) -> bool:
        """Detect system natural scrolling preference."""
        if not self.config.respect_system_preference:
            return False

        try:
            defaults = NSUserDefaults.standardUserDefaults()
            natural = defaults.boolForKey_("com.apple.swipescrolldirection")
            return bool(natural)
        except Exception:
            return False

    def cancel(self) -> None:
        """Cancel any ongoing scroll."""
        if self.is_scrolling:
            self.end_gesture()
