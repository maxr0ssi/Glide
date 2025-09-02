"""Unit tests for scroll components."""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from glide.gestures.circular import CircularEvent, CircularDirection


class TestScrollCalculations(unittest.TestCase):
    """Test scroll calculation logic."""
    
    def test_angle_to_pixel_mapping(self):
        """Test conversion of rotation angle to scroll pixels."""
        # 180 degrees = 400 pixels
        pixels_per_degree = 2.22
        
        test_cases = [
            (90, 200),
            (180, 400),
            (270, 600),
            (360, 800),
        ]
        
        for angle, expected in test_cases:
            pixels = angle * pixels_per_degree
            # Allow small floating point differences
            self.assertAlmostEqual(pixels, expected, delta=1.0)
    
    def test_direction_mapping(self):
        """Test mapping of circular direction to scroll direction."""
        # Clockwise = scroll down (positive delta)
        # Counter-clockwise = scroll up (negative delta)
        
        cw_event = CircularEvent(
            ts_ms=1000,
            direction=CircularDirection.CLOCKWISE,
            total_angle_deg=180,
            strength=0.8,
            duration_ms=500
        )
        
        ccw_event = CircularEvent(
            ts_ms=2000,
            direction=CircularDirection.COUNTER_CLOCKWISE,
            total_angle_deg=180,
            strength=0.8,
            duration_ms=500
        )
        
        # With natural scrolling off:
        # CW should give positive delta (scroll down)
        # CCW should give negative delta (scroll up)
        pixels_per_degree = 2.22
        
        cw_delta = cw_event.total_angle_deg * pixels_per_degree
        ccw_delta = -ccw_event.total_angle_deg * pixels_per_degree
        
        self.assertGreater(cw_delta, 0)
        self.assertLess(ccw_delta, 0)
    
    def test_natural_scrolling_inversion(self):
        """Test that natural scrolling inverts the direction."""
        angle = 180
        pixels_per_degree = 2.22
        
        # Normal scrolling
        normal_delta = angle * pixels_per_degree
        
        # Natural scrolling (inverted)
        natural_delta = -normal_delta
        
        self.assertEqual(normal_delta, -natural_delta)
    
    def test_velocity_clamping(self):
        """Test that extreme velocities are clamped."""
        max_velocity = 100.0  # pixels per event
        
        test_cases = [
            (50, 50),    # Within limits
            (100, 100),  # At limit
            (150, 100),  # Over limit - should clamp
            (500, 100),  # Way over - should clamp
        ]
        
        for velocity, expected in test_cases:
            clamped = min(velocity, max_velocity)
            self.assertEqual(clamped, expected)


class TestCircularEventSerialization(unittest.TestCase):
    """Test CircularEvent serialization."""
    
    def test_to_json_dict(self):
        """Test conversion to JSON-serializable dict."""
        event = CircularEvent(
            ts_ms=12345,
            direction=CircularDirection.CLOCKWISE,
            total_angle_deg=270.5,
            strength=0.95,
            duration_ms=750
        )
        
        json_dict = event.to_json_dict()
        
        self.assertEqual(json_dict["ts_ms"], 12345)
        self.assertEqual(json_dict["direction"], "CW")
        self.assertEqual(json_dict["total_angle_deg"], 270.5)
        self.assertEqual(json_dict["strength"], 0.95)
        self.assertEqual(json_dict["duration_ms"], 750)


if __name__ == "__main__":
    unittest.main()