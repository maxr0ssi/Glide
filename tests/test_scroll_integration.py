"""Test scroll integration by simulating circular events."""

import time
from glide.gestures.circular import CircularEvent, CircularDirection
from glide.runtime.actions.scroll import ScrollConfig, ScrollDispatcher


def test_scroll_integration():
    """Test the scroll dispatcher with simulated events."""
    print("Testing Scroll Integration")
    print("=" * 40)
    
    # Create config and dispatcher
    config = ScrollConfig(
        pixels_per_degree=2.22,
        max_velocity=100.0,
        respect_system_preference=True,
        show_hud=False  # No HUD for this test
    )
    
    dispatcher = ScrollDispatcher(config)
    
    if dispatcher.action is None:
        print("✗ Failed to initialize scroll action")
        return False
    
    print("✓ ScrollDispatcher initialized")
    
    # Test events
    test_events = [
        CircularEvent(
            ts_ms=1000,
            direction=CircularDirection.CLOCKWISE,
            total_angle_deg=90,  # Quarter turn = 200px
            strength=0.8,
            duration_ms=300
        ),
        CircularEvent(
            ts_ms=2000,
            direction=CircularDirection.COUNTER_CLOCKWISE,
            total_angle_deg=180,  # Half turn = 400px
            strength=0.9,
            duration_ms=500
        ),
        CircularEvent(
            ts_ms=3000,
            direction=CircularDirection.CLOCKWISE,
            total_angle_deg=360,  # Full turn = 800px (clamped to max)
            strength=0.95,
            duration_ms=800
        ),
    ]
    
    print("\nDispatching test events:")
    print("(Watch for actual scrolling in focused window)")
    
    for i, event in enumerate(test_events):
        print(f"\nEvent {i+1}:")
        print(f"  Direction: {event.direction.value}")
        print(f"  Angle: {event.total_angle_deg}°")
        print(f"  Expected pixels: {event.total_angle_deg * config.pixels_per_degree:.0f}")
        
        success = dispatcher.dispatch(event)
        print(f"  Dispatched: {'✓' if success else '✗'}")
        
        # Wait between events
        time.sleep(1.0)
    
    print("\n" + "=" * 40)
    print("Integration test complete")
    return True


if __name__ == "__main__":
    import sys
    success = test_scroll_integration()
    sys.exit(0 if success else 1)