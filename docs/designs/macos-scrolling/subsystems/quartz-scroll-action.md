# QuartzScrollAction Subsystem

## Purpose

QuartzScrollAction implements the platform-specific scroll behavior for macOS using the Quartz Event Services API. It translates high-level scroll commands into native CGEventRef objects that integrate seamlessly with macOS applications, respecting system preferences and providing smooth, momentum-based scrolling.

## Inputs / Outputs

### Inputs

```python
# From ScrollDispatcher via execute()
CircularEvent:
    direction: CircularDirection  # Determines scroll direction
    total_angle_deg: float       # Maps to scroll distance
    strength: float              # Influences momentum
    duration_ms: int             # For velocity calculation

# Configuration
ScrollConfig:
    pixels_per_degree: float     # Core mapping ratio
    max_velocity: float          # Velocity clamping
    acceleration_curve: float    # Non-linear scaling
    respect_system_preference: bool  # Natural scrolling
```

### Outputs

```python
# Direct system effects via CGEventPost
- Native scroll wheel events posted to active application
- Momentum scrolling initiated based on velocity
- System scroll indicators updated

# No return value (fire-and-forget pattern)
```

### Validation Rules

1. **Parameter Bounds**:
   - Scroll deltas clamped to [-max_velocity, +max_velocity]
   - Minimum delta of 1.0 pixel to trigger event
   - Maximum of 10 events per gesture to prevent overflow

2. **System State**:
   - Accessibility permission must be granted
   - Main thread execution required
   - Active display must be available

## Invariants

1. **Thread Affinity**: All Quartz API calls MUST execute on main thread
2. **Event Lifecycle**: Every CGEventRef must be released after posting
3. **Natural Scrolling**: System preference must be honored when configured
4. **Event Integrity**: Generated events must have valid source and flags
5. **Permission State**: Must not attempt event posting without permission

## Edge Cases

### Natural Scrolling Toggle
**Scenario**: User changes system preference while app is running
**Handling**:
- Detect via NSWorkspace notifications
- Update cached preference immediately
- Apply to next event (no retroactive changes)

### Permission Revoked Mid-Session
**Scenario**: User revokes accessibility permission while running
**Handling**:
- CGEventPost returns NULL
- Cache permission state as invalid
- Return early from execute() until restored
- Trigger one-time notification to user

### Extreme Velocity Values
**Scenario**: Calculated velocity exceeds system limits
**Handling**:
- Clamp to system maximum (±64 units per event)
- Split large scrolls into multiple events
- Maintain total distance accuracy

### Application Not Responding
**Scenario**: Target app is frozen or busy
**Handling**:
- Events queue in system event buffer
- No special handling needed (OS manages)
- Timeout handled by OS layer

### Multiple Displays
**Scenario**: User has multiple monitors
**Handling**:
- Post to kCGHIDEventTap (follows cursor)
- No display-specific targeting needed
- Works across display boundaries

## Dependencies

### System Frameworks (via PyObjC)
```python
import Quartz  # CGEventCreateScrollWheelEvent, CGEventPost
import AppKit  # NSUserDefaults for natural scrolling
from Quartz import (
    kCGScrollEventUnitPixel,
    kCGEventScrollWheel,
    kCGHIDEventTap,
    CGEventCreateScrollWheelEvent,
    CGEventPost
)
```

### Internal Dependencies
```python
from glide.runtime.actions.scroll import ScrollAction, ScrollConfig
from glide.gestures.circular import CircularEvent, CircularDirection
```

### System Requirements
- macOS 10.12+ (Sierra or later)
- PyObjC 8.0+ with Quartz framework
- Accessibility permission granted

## Test Matrix

| Test Case | Input | Expected Behavior | Verification Method |
|-----------|-------|-------------------|---------------------|
| **Basic Down Scroll** | CW, 90°, natural=false | Scroll down 200px | Event monitor capture |
| **Basic Up Scroll** | CCW, 90°, natural=false | Scroll up 200px | Event monitor capture |
| **Natural Scrolling** | CW, 90°, natural=true | Scroll up 200px | Direction inverted |
| **Momentum Scroll** | CW, 360°, 200ms | Initial + momentum | Multiple events captured |
| **Max Velocity** | CW, 720° | Clamped scroll | Delta ≤ max_velocity |
| **No Permission** | Any event | No scroll, log error | CGEventPost returns NULL |
| **Fractional Pixels** | 45° rotation | 100px scroll | Proper rounding |
| **Rapid Events** | 10 events < 100ms | All processed | No drops |
| **Zero Delta** | 0.1° rotation | No event posted | Skip small movements |
| **Thread Safety** | Off-main call | Dispatch to main | No crash |

## Implementation Notes

### Natural Scrolling Detection
```python
def _detect_natural_scrolling(self) -> bool:
    # Primary method: User defaults
    defaults = NSUserDefaults.standardUserDefaults()
    natural = defaults.boolForKey_("com.apple.swipescrolldirection")
    
    # Fallback: Check trackpad settings
    if natural is None:
        # Assume false if not set
        natural = False
    
    return natural
```

### Event Creation Pattern
```python
def _create_scroll_event(self, delta_x: float, delta_y: float) -> CGEventRef:
    # Create scroll wheel event
    # wheelCount: 2 for x,y support
    # wheel1: vertical (y) delta  
    # wheel2: horizontal (x) delta
    # wheel3: 0 (unused)
    event = CGEventCreateScrollWheelEvent(
        None,  # NULL source
        kCGScrollEventUnitPixel,  # Pixel units
        2,     # wheelCount
        int(delta_y),  # wheel1 (vertical)
        int(delta_x),  # wheel2 (horizontal)
    )
    
    # Set continuous gesture flag for momentum
    if abs(delta_y) > 20:
        CGEventSetIntegerValueField(
            event,
            kCGScrollWheelEventIsContinuous,
            1
        )
    
    return event
```

### Main Thread Execution
```python
def execute(self, event: CircularEvent) -> None:
    if not NSThread.isMainThread():
        # Dispatch to main thread
        dispatch_async(dispatch_get_main_queue(), 
                      lambda: self._execute_on_main(event))
    else:
        self._execute_on_main(event)
```

### Performance Optimizations

1. **Event Coalescing**: System automatically coalesces rapid scroll events
2. **Integer Deltas**: Round to integers for system compatibility
3. **Cached Preferences**: Natural scrolling checked once per session
4. **Minimal Allocations**: Reuse calculation buffers where possible

### Error Recovery

- **Permission Errors**: Graceful degradation, no repeated attempts
- **API Failures**: Log and skip event, continue processing
- **Thread Violations**: Auto-dispatch to main thread
- **Invalid Parameters**: Clamp to valid ranges, never crash

## Future Improvements

The following advanced features are deferred for post-POC implementation:

### System Preference Monitoring
```python
# Future: Real-time natural scrolling detection
NSWorkspace.sharedWorkspace().notificationCenter().addObserver_selector_name_object_(
    self,
    self.naturalScrollingChanged_,
    NSUserDefaultsDidChangeNotification,
    None
)
```

### Advanced Thread Management
- Automatic main thread dispatch with GCD
- Thread-safe event queuing
- Async event posting with callbacks
- Thread pool for parallel processing

### Momentum & Physics
- Gesture velocity to momentum mapping
- Inertial scrolling calculations
- Spring physics for rubber-band effects
- Gesture continuation detection

### Performance Optimizations
- Event coalescing at system level
- Cached CGEventRef object pooling
- Minimal allocation strategies
- Profile-guided optimization

### Enhanced Error Handling
- Permission state caching and monitoring
- Retry logic for transient failures
- User notification system
- Diagnostic logging with telemetry

### Platform Integration
- Per-application scroll profiles
- Multi-touch gesture support
- Trackpad gesture coordination
- Accessibility API integration

### POC Simplifications
For the proof of concept, we implement:
- Basic CGEventCreateScrollWheelEvent usage
- One-time natural scrolling detection
- Simple error logging to console
- Direct event posting without queuing
- Trust caller for main thread execution