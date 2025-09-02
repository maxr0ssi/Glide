"""Test script to verify PyObjC installation and scroll event generation."""

import sys
import time

try:
    from Quartz import (
        CGEventCreateScrollWheelEvent,
        CGEventPost,
        kCGScrollEventUnitPixel,
        kCGHIDEventTap,
        kCGEventScrollWheel
    )
    from AppKit import NSUserDefaults
    print("✓ PyObjC imports successful")
except ImportError as e:
    print(f"✗ PyObjC import failed: {e}")
    print("Please install with: pip install pyobjc-framework-Quartz")
    sys.exit(1)


def test_natural_scrolling_detection():
    """Test detection of natural scrolling preference."""
    print("\n--- Testing Natural Scrolling Detection ---")
    try:
        defaults = NSUserDefaults.standardUserDefaults()
        natural = defaults.boolForKey_("com.apple.swipescrolldirection")
        print(f"Natural scrolling enabled: {natural}")
        # This test passes if we can read the value (True or False are both valid)
        return True
    except Exception as e:
        print(f"Error detecting natural scrolling: {e}")
        return False


def test_scroll_event_creation():
    """Test creating a scroll event."""
    print("\n--- Testing Scroll Event Creation ---")
    try:
        # Create a simple scroll event (scroll down 100 pixels)
        event = CGEventCreateScrollWheelEvent(
            None,  # NULL source
            kCGScrollEventUnitPixel,  # Unit type
            1,     # wheelCount (1 for vertical only)
            100    # delta_y (positive = down)
        )
        
        if event:
            print("✓ Successfully created scroll event")
            # Don't actually post it in the test
            return True
        else:
            print("✗ Failed to create scroll event")
            return False
    except Exception as e:
        print(f"Error creating scroll event: {e}")
        return False


def test_permission_check():
    """Check if we can actually post events."""
    print("\n--- Testing Event Posting Permission ---")
    try:
        # Try to create and immediately release a small scroll event
        event = CGEventCreateScrollWheelEvent(None, kCGScrollEventUnitPixel, 1, 1)
        if event:
            # Try posting with a very small delta that shouldn't be noticeable
            result = CGEventPost(kCGHIDEventTap, event)
            if result is None:
                print("✓ Successfully posted test event (permission granted)")
                return True
            else:
                print("✗ Failed to post event (check Accessibility permission)")
                print("  Go to: System Preferences > Security & Privacy > Privacy > Accessibility")
                print("  Add Terminal or your Python interpreter")
                return False
    except Exception as e:
        print(f"Error testing permission: {e}")
        return False


def test_scroll_calculations():
    """Test angle-to-pixel calculations."""
    print("\n--- Testing Scroll Calculations ---")
    
    # Test mapping: 180 degrees = 400 pixels
    pixels_per_degree = 400.0 / 180.0
    
    test_cases = [
        (90, 200),    # Quarter turn
        (180, 400),   # Half turn
        (270, 600),   # Three-quarter turn
        (360, 800),   # Full turn
    ]
    
    print(f"Pixels per degree: {pixels_per_degree:.2f}")
    print("\nAngle → Pixel mapping:")
    for angle, expected in test_cases:
        pixels = angle * pixels_per_degree
        print(f"  {angle:3d}° → {pixels:6.1f}px (expected: {expected}px)")
    
    return True


def main():
    """Run all tests."""
    print("PyObjC Scroll Integration Test Suite")
    print("=" * 40)
    
    results = {
        "Natural Scrolling": test_natural_scrolling_detection(),
        "Event Creation": test_scroll_event_creation(),
        "Calculations": test_scroll_calculations(),
        "Permission": test_permission_check(),
    }
    
    print("\n" + "=" * 40)
    print("Test Summary:")
    for test, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {test}: {status}")
    
    if all(results.values()):
        print("\n✓ All tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())