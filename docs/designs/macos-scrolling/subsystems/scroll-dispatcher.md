# ScrollDispatcher Subsystem

## Purpose

The ScrollDispatcher serves as the central coordination point for translating circular gesture events into platform-specific scroll actions. It maintains configuration state, handles event routing, and ensures proper lifecycle management of scroll operations.

## Inputs / Outputs

### Inputs

```python
# Primary Input: Circular gesture events
CircularEvent:
    ts_ms: int              # Event timestamp
    direction: CircularDirection  # CW or CCW
    total_angle_deg: float  # Total rotation angle
    strength: float         # Gesture confidence (0.0-1.0)
    duration_ms: int        # Gesture duration

# Configuration Input
ScrollConfig:
    pixels_per_degree: float      # Angle to pixel mapping ratio
    max_velocity: float           # Maximum scroll velocity cap
    acceleration_curve: float     # Exponential acceleration factor
    respect_system_preference: bool  # Honor natural scrolling
    show_hud: bool               # Display visual feedback
    hud_fade_duration_ms: int    # HUD fade timing
```

### Outputs

```python
# Return value from dispatch()
success: bool  # True if event was processed successfully

# Side effects via ScrollAction
- Native scroll events posted to system
- HUD updates triggered
- Performance metrics logged
```

### Validation Rules

1. **Event Validation**:
   - `total_angle_deg` must be positive
   - `strength` must be in range [0.0, 1.0]
   - `duration_ms` must be positive
   - Events older than 1 second are rejected

2. **Configuration Validation**:
   - `pixels_per_degree` must be in range [0.1, 10.0]
   - `max_velocity` must be in range [10.0, 500.0]
   - `acceleration_curve` must be in range [1.0, 3.0]

## Invariants

1. **Single Instance**: Only one ScrollDispatcher should exist per application instance
2. **Thread Safety**: All public methods must be thread-safe
3. **Event Ordering**: Events must be processed in timestamp order
4. **Resource Lifecycle**: ScrollAction must be properly initialized before first dispatch
5. **Configuration Consistency**: Config updates must be atomic

## Edge Cases

### Rapid Gesture Changes
**Scenario**: User rapidly alternates between CW and CCW gestures
**Handling**: 
- Cancel any pending momentum scrolling
- Apply direction change immediately
- No cooldown between direction changes

### Configuration Update During Scroll
**Scenario**: Config updated while scroll animation is active
**Handling**:
- Current scroll completes with old config
- New config applies to next event
- No interruption of user experience

### Missing Accessibility Permission
**Scenario**: ScrollAction cannot post events due to permissions
**Handling**:
- Log warning with permission instructions
- Return False from dispatch()
- Queue up to 10 events for retry
- Show permission dialog once per session

### Extreme Rotation Angles
**Scenario**: User rotates > 720 degrees in single gesture
**Handling**:
- Clamp to max_velocity to prevent overflow
- Apply logarithmic dampening for extreme angles
- Split into multiple scroll events if needed

### Zero Duration Events
**Scenario**: Event reports duration_ms = 0
**Handling**:
- Calculate velocity using minimum duration of 16ms
- Log anomaly for debugging
- Process event normally otherwise

## Dependencies

### Internal Dependencies
```python
from glide.gestures.circular import CircularEvent, CircularDirection
from glide.runtime.actions.scroll import ScrollAction, ScrollConfig
from glide.runtime.ui.scroll_hud import ScrollHUD
```

### External Dependencies
- `threading.Lock` for thread safety
- `time.time()` for timestamp validation
- `logging` for error reporting

### Platform Dependencies
- Concrete ScrollAction implementation (e.g., QuartzScrollAction)
- Platform-specific HUD implementation

## Test Matrix

| Test Case | Input | Expected Output | Notes |
|-----------|-------|-----------------|-------|
| **Basic CW Scroll** | CW event, 180° | Scroll down 400px | Verify pixel mapping |
| **Basic CCW Scroll** | CCW event, 90° | Scroll up 200px | Half rotation |
| **Natural Scrolling** | CW event, natural=true | Scroll up | Direction inverted |
| **Max Velocity Clamp** | CW event, 720° | Scroll at max_velocity | No overflow |
| **Stale Event** | Event > 1s old | Return False | Rejection logged |
| **Config Update** | Update during idle | New config active | No side effects |
| **Permission Denied** | No accessibility | Return False | Show dialog once |
| **Rapid Direction Change** | CW→CCW quickly | Immediate reversal | No momentum carry |
| **Invalid Strength** | strength = 1.5 | Clamped to 1.0 | Validation active |
| **Zero Duration** | duration = 0 | Uses 16ms minimum | No division by zero |

## Implementation Notes

### State Management
```python
class ScrollDispatcher:
    def __init__(self):
        self._lock = threading.Lock()
        self._last_direction = None
        self._last_event_time = 0
        self._momentum_active = False
        self._event_queue = deque(maxlen=10)
        self._permission_checked = False
```

### Event Processing Pipeline
1. Validate event freshness and parameters
2. Check and update permission state if needed
3. Calculate scroll delta based on angle and config
4. Apply acceleration curve for large angles
5. Respect natural scrolling preference
6. Dispatch to platform action
7. Update HUD if enabled
8. Log metrics for analysis

### Error Handling Strategy
- All exceptions caught and logged at dispatch boundary
- Failed dispatches return False but don't crash
- Persistent failures trigger graceful degradation
- User notification for permission issues only

## Future Improvements

The following advanced features are deferred for post-POC implementation:

### Thread Safety & State Management
```python
# Future: Thread-safe implementation with locks
self._lock = threading.Lock()
self._event_queue = deque(maxlen=10)
self._momentum_active = False
```

### Event Validation & Ordering
- Comprehensive parameter validation with bounds checking
- Event freshness validation (reject >1 second old)
- Timestamp-based event ordering guarantees
- Queue overflow protection mechanisms

### Advanced Error Recovery
- Event retry queue for transient failures
- Permission state monitoring and caching
- Graceful degradation with user notifications
- Automatic recovery attempts

### Performance Features
- Event coalescing for rapid gesture sequences
- Momentum tracking and prediction
- CPU usage monitoring and throttling
- Memory-efficient event pooling

### Configuration Management
- Atomic configuration updates
- Runtime configuration hot-reloading
- Per-application profiles
- User preference persistence

### POC Simplifications
For the proof of concept, we implement:
- Direct event dispatch (no queuing)
- Simple console logging for errors
- Basic configuration from defaults.yaml
- Synchronous processing without locks
- Trust gesture detector for valid events