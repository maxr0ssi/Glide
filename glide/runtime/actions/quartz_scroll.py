"""macOS-specific scroll implementation using Quartz Event Services."""

from __future__ import annotations

from typing import Tuple
import platform

if platform.system() != "Darwin":
    raise ImportError("QuartzScrollAction is only available on macOS")

try:
    from Quartz import (
        CGEventCreateScrollWheelEvent,
        CGEventPost,
        kCGScrollEventUnitPixel,
        kCGHIDEventTap,
        CGEventSetIntegerValueField,
        kCGScrollWheelEventIsContinuous
    )
    from AppKit import NSUserDefaults, NSThread
except ImportError as e:
    raise ImportError(f"PyObjC is required for QuartzScrollAction: {e}")

from glide.runtime.actions.scroll import ScrollAction, ScrollConfig
from glide.gestures.circular import CircularEvent, CircularDirection


class QuartzScrollAction(ScrollAction):
    """macOS-specific scroll implementation using Quartz Event Services.
    
    POC Implementation:
    - Basic CGEventCreateScrollWheelEvent usage
    - One-time natural scrolling detection
    - Simple error logging
    - Direct event posting (no queuing)
    """
    
    def __init__(self, config: ScrollConfig):
        """Initialize with configuration and system preference detection."""
        self.config = config
        self._natural_scrolling = self._detect_natural_scrolling()
        self._permission_checked = False
        
        # Initialized with natural scrolling detection
    
    def execute(self, event: CircularEvent) -> None:
        """
        Generate CGScrollWheelEvent based on circular gesture.
        
        Maps circular motion to scroll delta:
        - Clockwise → Scroll down (positive delta)
        - Counter-clockwise → Scroll up (negative delta)
        - Respects natural scrolling preference
        """
        # Calculate scroll delta
        delta_x, delta_y = self._calculate_scroll_delta(event)
        
        # Create and post the scroll event
        try:
            scroll_event = self._create_scroll_event(delta_x, delta_y)
            if scroll_event:
                CGEventPost(kCGHIDEventTap, scroll_event)
                # No need to release in Python - handled by PyObjC
            else:
                pass  # Failed to create scroll event
        except Exception as e:
            if not self._permission_checked:
                # Show user-friendly error message on first occurrence
                import sys
                sys.stderr.write("\nError: Unable to generate scroll events.\n")
                sys.stderr.write("Please grant Accessibility permission:\n")
                sys.stderr.write("  1. Open System Preferences > Security & Privacy > Privacy > Accessibility\n")
                sys.stderr.write("  2. Add Terminal (or your IDE) to the allowed apps\n")
                sys.stderr.write("  3. Restart Glide\n\n")
                self._permission_checked = True
    
    def cancel(self) -> None:
        """Cancel any ongoing momentum scrolling."""
        # POC: No momentum implementation yet
        pass
    
    def _calculate_scroll_delta(self, event: CircularEvent) -> Tuple[float, float]:
        """
        Calculate scroll delta from circular event.
        
        Returns:
            (delta_x, delta_y) in pixels, respecting natural scrolling
        """
        # Basic angle to pixel conversion
        pixels = event.total_angle_deg * self.config.pixels_per_degree
        
        # Apply velocity clamping
        pixels = min(pixels, self.config.max_velocity)
        
        # Determine scroll direction
        # Clockwise = positive delta (scroll down)
        # Counter-clockwise = negative delta (scroll up)
        if event.direction == CircularDirection.CLOCKWISE:
            delta_y = pixels
        else:
            delta_y = -pixels
        
        # Apply natural scrolling if enabled
        if self.config.respect_system_preference and self._natural_scrolling:
            delta_y = -delta_y
        
        # No horizontal scrolling in POC
        delta_x = 0.0
        
        return (delta_x, delta_y)
    
    def _detect_natural_scrolling(self) -> bool:
        """Detect system natural scrolling preference."""
        if not self.config.respect_system_preference:
            return False
        
        try:
            defaults = NSUserDefaults.standardUserDefaults()
            # This key stores the natural scrolling preference
            # True = natural scrolling enabled (reversed)
            natural = defaults.boolForKey_("com.apple.swipescrolldirection")
            return bool(natural)
        except Exception as e:
            # Error detecting natural scrolling preference
            # Default to non-natural scrolling if detection fails
            return False
    
    def _create_scroll_event(self, delta_x: float, delta_y: float) -> object:
        """Create native scroll event."""
        try:
            # Create scroll wheel event
            # Parameters:
            # - source: None (NULL)
            # - units: kCGScrollEventUnitPixel (pixel-based scrolling)
            # - wheelCount: 1 (vertical scrolling only for POC)
            # - wheel1: vertical delta
            event = CGEventCreateScrollWheelEvent(
                None,  # NULL source
                kCGScrollEventUnitPixel,  # Unit type
                1,     # wheelCount (1 for vertical only)
                int(delta_y)  # wheel1 (vertical)
            )
            
            # Mark as continuous gesture for smoother scrolling
            if event and abs(delta_y) > 20:
                try:
                    CGEventSetIntegerValueField(
                        event,
                        kCGScrollWheelEventIsContinuous,
                        1
                    )
                except:
                    # Not critical if this fails
                    pass
            
            return event
        except Exception as e:
            # Error creating scroll event
            return None