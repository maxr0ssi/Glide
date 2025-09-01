# macOS Scrolling — Technical Design

*Version 1.0.0 · Updated 2025-09-01*

## Context & Goals

This design implements macOS scrolling control based on circular gestures as specified in [docs/proposals/macos-scrolling.md](/Users/maxrossi/Documents/Glide/docs/proposals/macos-scrolling.md).

**Primary Goal**: Bridge the gap between detected circular gestures and native macOS scroll events, enabling hands-free document navigation.

**Success Criteria**:
- Latency < 150ms from gesture start to first scroll event
- Smooth, natural scrolling matching finger rotation speed
- 95%+ accuracy for intentional gestures
- < 1 false positive per 5-minute session
- < 5% additional CPU overhead

## Architecture Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ CircularDetector │────>│ ScrollDispatcher │────>│ QuartzEventAPI  │
│                  │     │                  │     │                  │
│ Emits:           │     │ Receives:        │     │ Generates:      │
│ CircularEvent    │     │ - CircularEvent  │     │ CGScrollEvent   │
└─────────────────┘     │ - Config         │     └─────────────────┘
                        │                  │
                        │ Maps:            │     ┌─────────────────┐
                        │ - Angle→Pixels   │────>│ ScrollHUD       │
                        │ - Direction      │     │                 │
                        └──────────────────┘     │ Shows:          │
                                                │ - Direction     │
                                                │ - Velocity      │
                                                └─────────────────┘
```

**Data Flow**:
1. `CircularDetector` emits `CircularEvent` with angle, direction, and duration
2. `ScrollDispatcher` receives events and maps them to scroll parameters
3. Dispatcher uses `QuartzEventAPI` to generate native scroll events
4. Optional `ScrollHUD` provides visual feedback during scrolling

## Public Interfaces

### ScrollDispatcher

```python
# glide/runtime/actions/scroll.py

from typing import Optional, Protocol
from dataclasses import dataclass
from glide.gestures.circular import CircularEvent

@dataclass
class ScrollConfig:
    """Configuration for scroll behavior."""
    # Mapping: 180 degrees ≈ 400 pixels
    pixels_per_degree: float = 2.22  # 400/180
    
    # Smooth scrolling parameters
    max_velocity: float = 100.0  # pixels per event
    acceleration_curve: float = 1.5  # exponential factor
    
    # Natural scrolling preference
    respect_system_preference: bool = True
    
    # HUD display
    show_hud: bool = True
    hud_fade_duration_ms: int = 500


class ScrollAction(Protocol):
    """Protocol for scroll action implementations."""
    
    def execute(self, event: CircularEvent) -> None:
        """Execute scroll action based on circular event."""
        ...
    
    def cancel(self) -> None:
        """Cancel any ongoing scroll animations."""
        ...


class ScrollDispatcher:
    """Dispatches circular events to platform-specific scroll actions."""
    
    def __init__(self, config: ScrollConfig, action: Optional[ScrollAction] = None):
        """
        Initialize dispatcher with configuration.
        
        Args:
            config: Scroll behavior configuration
            action: Platform-specific scroll implementation (auto-detected if None)
        """
        ...
    
    def dispatch(self, event: CircularEvent) -> bool:
        """
        Dispatch circular event to scroll action.
        
        Args:
            event: Circular gesture event to process
            
        Returns:
            True if event was handled, False otherwise
        """
        ...
    
    def update_config(self, config: ScrollConfig) -> None:
        """Update runtime configuration."""
        ...
```

### QuartzScrollAction

```python
# glide/runtime/actions/quartz_scroll.py

from typing import Tuple
import Quartz
from glide.runtime.actions.scroll import ScrollAction, ScrollConfig
from glide.gestures.circular import CircularEvent, CircularDirection

class QuartzScrollAction(ScrollAction):
    """macOS-specific scroll implementation using Quartz Event Services."""
    
    def __init__(self, config: ScrollConfig):
        """Initialize with configuration and system preference detection."""
        self.config = config
        self._natural_scrolling = self._detect_natural_scrolling()
        self._current_animation = None
    
    def execute(self, event: CircularEvent) -> None:
        """
        Generate CGScrollWheelEvent based on circular gesture.
        
        Maps circular motion to scroll delta:
        - Clockwise → Scroll down (positive delta)
        - Counter-clockwise → Scroll up (negative delta)
        - Respects natural scrolling preference
        """
        ...
    
    def cancel(self) -> None:
        """Cancel any ongoing momentum scrolling."""
        ...
    
    def _calculate_scroll_delta(self, event: CircularEvent) -> Tuple[float, float]:
        """
        Calculate scroll delta from circular event.
        
        Returns:
            (delta_x, delta_y) in pixels, respecting natural scrolling
        """
        ...
    
    def _detect_natural_scrolling(self) -> bool:
        """Detect system natural scrolling preference."""
        ...
    
    def _create_scroll_event(self, delta_x: float, delta_y: float) -> Quartz.CGEventRef:
        """Create native scroll event."""
        ...
```

### ScrollHUD

```python
# glide/runtime/ui/scroll_hud.py

from dataclasses import dataclass
from typing import Optional
import tkinter as tk
from glide.gestures.circular import CircularDirection

@dataclass
class HUDMetrics:
    """Visual metrics for HUD display."""
    window_width: int = 120
    window_height: int = 60
    opacity: float = 0.8
    fade_duration_ms: int = 500
    position: str = "bottom-right"  # bottom-right, bottom-center, etc.


class ScrollHUD:
    """Minimal overlay showing scroll direction and velocity."""
    
    def __init__(self, metrics: HUDMetrics):
        """Initialize HUD with display metrics."""
        self.metrics = metrics
        self._window: Optional[tk.Toplevel] = None
        self._fade_timer = None
    
    def show_scroll(self, direction: CircularDirection, velocity: float) -> None:
        """
        Display scroll indicator.
        
        Args:
            direction: Scroll direction (CW/CCW)
            velocity: Normalized velocity (0.0-1.0)
        """
        ...
    
    def hide(self) -> None:
        """Hide HUD with fade animation."""
        ...
    
    def _create_window(self) -> None:
        """Create transparent overlay window."""
        ...
    
    def _update_display(self, direction: CircularDirection, velocity: float) -> None:
        """Update HUD content."""
        ...
```

## Data Model

### Event Extensions

```python
# Extension to CircularEvent for scroll context
@dataclass
class ScrollContext:
    """Additional context for scroll events."""
    # Cumulative angle for momentum calculation
    cumulative_angle: float = 0.0
    
    # Time since last event for acceleration
    time_delta_ms: int = 0
    
    # Detected gesture velocity (degrees/second)
    angular_velocity: float = 0.0
    
    # Platform-specific modifiers
    modifiers: int = 0  # Shift, Cmd, etc.
```

### Configuration Schema

```yaml
# Addition to AppConfig
scroll:
  enabled: bool = True
  pixels_per_degree: float = 2.22
  max_velocity: float = 100.0
  acceleration_curve: float = 1.5
  respect_system_preference: bool = True
  show_hud: bool = True
  hud_fade_duration_ms: int = 500
  hud_position: str = "bottom-right"
```

## Invariants & Failure Modes

### System Invariants

1. **Single Dispatcher**: Only one ScrollDispatcher instance should be active
2. **Event Ordering**: Scroll events must be dispatched in the order received
3. **Resource Cleanup**: All Quartz events must be properly released
4. **Thread Safety**: All Quartz API calls must happen on the main thread
5. **Permission State**: Accessibility permission must be granted before first use

### Failure Modes & Mitigations

| Failure Mode | Detection | Mitigation |
|-------------|-----------|------------|
| **No Accessibility Permission** | `AXIsProcessTrusted() == false` | Show permission dialog, disable scrolling until granted |
| **Quartz API Failure** | `CGEventPost` returns error | Log error, skip event, continue processing |
| **Natural Scrolling Detection Fails** | `NSUserDefaults` returns nil | Default to non-natural scrolling |
| **HUD Creation Fails** | Tkinter exception | Disable HUD, continue with scrolling |
| **Event Queue Overflow** | > 100 pending events | Drop oldest events, log warning |
| **Gesture-Scroll Mismatch** | User reports inverted scrolling | Provide manual direction override |

### Error Recovery Strategy

```python
class ScrollErrorHandler:
    """Centralized error handling for scroll subsystem."""
    
    def handle_permission_error(self) -> None:
        """Guide user through accessibility permission setup."""
        # 1. Check current permission state
        # 2. Show system preferences if needed
        # 3. Provide clear instructions
        # 4. Retry after user action
    
    def handle_api_error(self, error: Exception) -> None:
        """Handle Quartz API failures gracefully."""
        # 1. Log detailed error context
        # 2. Attempt recovery if transient
        # 3. Disable feature if persistent
        # 4. Notify user of degraded state
```

## Security & Privacy

1. **Accessibility Permission**: Required for CGEventPost
   - Check permission state on startup
   - Provide clear explanation why needed
   - Never attempt to bypass permission system

2. **Event Injection Safety**:
   - Only inject scroll events, never keyboard/mouse clicks
   - Validate all parameters before event creation
   - Rate limit to prevent abuse (max 60 events/second)

3. **Privacy Considerations**:
   - No logging of scrolled content
   - No tracking of application context
   - Events are fire-and-forget

## Performance Considerations

1. **Event Generation**: Use `CGEventPost` with `kCGHIDEventTap` for lowest latency
2. **Momentum Scrolling**: Leverage native momentum by sending initial velocity
3. **CPU Usage**: Batch events when possible, use native event coalescing
4. **Memory**: Event objects must be released immediately after posting

## Test Strategy

### Unit Tests

```python
# tests/runtime/actions/test_scroll_dispatcher.py
- test_dispatch_clockwise_scroll_down()
- test_dispatch_counterclockwise_scroll_up()
- test_respect_natural_scrolling_preference()
- test_angle_to_pixel_mapping()
- test_max_velocity_clamping()
- test_config_update_runtime()

# tests/runtime/actions/test_quartz_scroll.py
- test_event_creation_valid_parameters()
- test_natural_scrolling_detection()
- test_scroll_delta_calculation()
- test_error_handling_no_permission()
- test_thread_safety_main_thread_only()
```

### Integration Tests

```python
# tests/integration/test_scroll_integration.py
- test_circular_to_scroll_pipeline()
- test_scroll_latency_under_150ms()
- test_continuous_scroll_smoothness()
- test_hud_display_coordination()
- test_permission_dialog_flow()
```

### Architecture Tests

```python
# tests/architecture/test_scroll_architecture.py
- test_no_direct_quartz_imports_outside_runtime()
- test_scroll_dispatcher_singleton_enforcement()
- test_config_schema_compatibility()
- test_public_api_surface_minimal()
```

### Manual Test Scenarios

1. **Basic Scrolling**:
   - Clockwise gesture → Page scrolls down
   - Counter-clockwise → Page scrolls up
   - Verify 180° ≈ 400 pixels movement

2. **Natural Scrolling**:
   - Toggle system preference
   - Verify direction flips appropriately

3. **Application Compatibility**:
   - Test in Preview, Safari, Chrome
   - Verify smooth scrolling in each

4. **Performance**:
   - Monitor CPU during extended sessions
   - Verify < 5% overhead
   - Check memory stability

## Test Scaffolds

```
tests/
├── runtime/
│   ├── actions/
│   │   ├── test_scroll_dispatcher.py
│   │   ├── test_quartz_scroll.py
│   │   └── fixtures/
│   │       └── mock_circular_events.py
│   └── ui/
│       └── test_scroll_hud.py
├── integration/
│   ├── test_scroll_integration.py
│   └── fixtures/
│       └── scroll_test_app.py
└── architecture/
    └── test_scroll_architecture.py
```

## Open Questions & Risks

### Open Questions

1. **Momentum Scrolling**: Should we implement gesture-based momentum or rely on system momentum?
2. **Multi-finger Scrolling**: Future support for two-finger scroll speed modulation?
3. **Horizontal Scrolling**: When to add support for horizontal scrolling?

### Technical Risks

1. **macOS Version Compatibility**: Quartz APIs may change in future macOS versions
   - Mitigation: Version detection and compatibility layer

2. **Permission Revocation**: User may revoke accessibility permission while running
   - Mitigation: Monitor permission state, graceful degradation

3. **App-Specific Behavior**: Some apps may not respond to synthetic scroll events
   - Mitigation: Document known incompatibilities, provide alternatives

## Future Improvements

The following features are designed but deferred for post-POC implementation:

### Thread Safety & Concurrency
- Full thread-safe implementation with locks and queues
- Event ordering guarantees with timestamp sorting
- Concurrent event processing pipeline
- Main thread dispatch automation

### Advanced Error Handling
- Permission state monitoring with recovery
- Event retry queue (up to 10 events)
- Graceful degradation strategies
- User notification dialogs for errors

### Event Validation & Processing
- Comprehensive input validation rules
- Stale event rejection (>1 second old)
- Event queue overflow protection
- Parameter bounds checking and clamping

### Architecture Tests
- Layering enforcement tests
- Public API surface validation
- Singleton pattern enforcement
- Cross-module dependency checks

### Performance Optimizations
- Event coalescing for rapid gestures
- Momentum scrolling calculations
- CPU usage profiling and optimization
- Memory pooling for event objects

### Advanced Configuration
- Per-app scroll speed customization
- Dynamic configuration reloading
- User preference profiles
- Gesture sensitivity tuning

## Implementation Notes

### Phase 1: Core Scrolling (2 days)
- Implement ScrollDispatcher and QuartzScrollAction
- Basic angle-to-pixel mapping
- Natural scrolling detection

### Phase 2: Polish & HUD (1 day)
- Add ScrollHUD with fade animations
- Fine-tune acceleration curves
- Error handling and recovery

### Phase 3: Testing & Integration (1 day)
- Comprehensive test suite
- Integration with main app pipeline
- Performance optimization

## Handoff Notes

**For Documenting Agent**:
- Create implementation template for `glide/runtime/` package structure
- Document Accessibility permission setup flow
- Add scroll configuration to user guide

**For Testing Agent**:
- Generate mock Quartz event fixtures
- Create automated permission state tests
- Build performance benchmarking suite

**For Implementation Team**:
- PyObjC installation required: `pip install pyobjc-framework-Quartz`
- Main thread execution critical for Quartz APIs
- Consider NSApplication vs pure Quartz for HUD implementation