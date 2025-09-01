# ScrollHUD Subsystem

## Purpose

ScrollHUD provides minimal, non-intrusive visual feedback during scroll operations. It displays the scroll direction and velocity using a transparent overlay that appears during scrolling and fades out when complete, helping users understand the gesture-to-scroll mapping without disrupting their workflow.

## Inputs / Outputs

### Inputs

```python
# Display trigger from ScrollDispatcher
show_scroll(
    direction: CircularDirection,  # CW or CCW
    velocity: float               # Normalized 0.0-1.0
)

# Configuration
HUDMetrics:
    window_width: int = 120       # Overlay width in pixels
    window_height: int = 60       # Overlay height in pixels
    opacity: float = 0.8          # Window transparency
    fade_duration_ms: int = 500   # Fade out animation time
    position: str = "bottom-right" # Screen position
```

### Outputs

```python
# Visual output only
- Transparent window overlay
- Direction indicator (↑ or ↓)
- Velocity visualization (bar graph)
- Fade in/out animations

# No programmatic return values
```

### Validation Rules

1. **Display Parameters**:
   - Velocity clamped to [0.0, 1.0]
   - Position must be valid screen location
   - Opacity must be in range [0.1, 1.0]

2. **Timing Constraints**:
   - Minimum display time: 100ms
   - Maximum display time: 2000ms
   - Fade animation must complete

## Invariants

1. **Single Window**: Only one HUD window exists at any time
2. **Non-Interactive**: HUD must not capture mouse/keyboard events
3. **Always Visible**: HUD must stay above other windows when active
4. **Thread Safety**: All UI updates must happen on main thread
5. **Resource Cleanup**: Window must be properly destroyed on exit

## Edge Cases

### Rapid Direction Changes
**Scenario**: Direction changes before fade completes
**Handling**:
- Cancel current fade animation
- Update display immediately
- Reset fade timer
- Smooth transition between states

### Multiple Display Configuration
**Scenario**: User has multiple monitors
**Handling**:
- Detect primary display on init
- Position relative to active display
- Reposition if display arrangement changes
- Fallback to primary if position invalid

### Window Manager Conflicts
**Scenario**: Other apps using similar overlay position
**Handling**:
- Use highest window level available
- Offset position if overlap detected
- Allow position configuration
- Never fight for focus

### System Dark Mode
**Scenario**: User toggles between light/dark mode
**Handling**:
- Detect system appearance
- Adapt colors for visibility
- White on dark, black on light
- Subtle drop shadow for contrast

### Low Memory Conditions
**Scenario**: System under memory pressure
**Handling**:
- Minimal memory footprint
- Release resources eagerly
- Disable if allocation fails
- No impact on core scrolling

## Dependencies

### UI Framework Options

```python
# Option 1: Tkinter (bundled with Python)
import tkinter as tk
from tkinter import ttk

# Option 2: PyObjC NSWindow (more native)
from AppKit import NSWindow, NSView, NSColor

# Option 3: PyQt (if already in use)
# from PyQt5.QtWidgets import QWidget
```

### Internal Dependencies
```python
from glide.gestures.circular import CircularDirection
from threading import Timer
import platform  # For macOS version detection
```

### System Requirements
- macOS 10.12+ for transparency support
- Python tkinter or PyObjC
- Core Graphics for screen info

## Test Matrix

| Test Case | Input | Expected Display | Verification |
|-----------|-------|------------------|--------------|
| **Show Down Arrow** | CW, velocity=0.5 | ↓ with 50% bar | Visual check |
| **Show Up Arrow** | CCW, velocity=1.0 | ↑ with 100% bar | Visual check |
| **Fade Animation** | Any, then idle | Fades after 500ms | Timer verify |
| **Rapid Updates** | 10 updates < 1s | Smooth transitions | No flicker |
| **Position Bottom Right** | position="bottom-right" | 20px from edges | Measure coords |
| **Dark Mode** | System dark mode | White indicators | Contrast check |
| **Multi-Monitor** | 2+ displays | Shows on active | Display query |
| **Memory Pressure** | Low memory | Graceful disable | No crash |
| **Concurrent Calls** | Threaded updates | Sequential display | Thread test |
| **Window Cleanup** | App exit | Window destroyed | Process check |

## Implementation Notes

### Window Creation Strategy
```python
def _create_window(self) -> None:
    # Tkinter approach for simplicity
    self._root = tk.Tk()
    self._root.withdraw()  # Hide root
    
    self._window = tk.Toplevel(self._root)
    self._window.overrideredirect(True)  # No decorations
    self._window.attributes('-topmost', True)  # Stay on top
    self._window.attributes('-alpha', self.metrics.opacity)
    
    # Make click-through
    self._window.attributes('-transparentcolor', 'white')
    self._window.config(bg='white')
    
    # Position window
    self._position_window()
```

### Visual Design
```
+------------------+
|                  |
|       ↓          |  Direction indicator
|   ████████       |  Velocity bar (filled based on speed)
|                  |
+------------------+
```

### Animation System
```python
def _fade_out(self) -> None:
    steps = 10
    delay = self.metrics.fade_duration_ms / steps / 1000
    
    def fade_step(remaining):
        if remaining <= 0:
            self.hide()
            return
        
        opacity = self.metrics.opacity * (remaining / steps)
        self._window.attributes('-alpha', opacity)
        self._window.after(int(delay * 1000), 
                          lambda: fade_step(remaining - 1))
    
    fade_step(steps)
```

### Performance Considerations

1. **Lightweight Rendering**: Use simple shapes, no images
2. **Hardware Acceleration**: Leverage system compositor
3. **Lazy Initialization**: Create window only on first use
4. **Resource Pooling**: Reuse window instead of recreating

### Platform Integration

```python
# Detect system appearance
def _get_system_appearance(self) -> str:
    if platform.mac_ver()[0] >= '10.14':  # Mojave+
        # Check for dark mode
        from subprocess import check_output
        result = check_output(['defaults', 'read', '-g', 
                              'AppleInterfaceStyle'])
        return 'dark' if b'Dark' in result else 'light'
    return 'light'  # Pre-Mojave default
```

### Error Handling

- **Window Creation Failure**: Log error, disable HUD
- **Display Detection Failure**: Use hardcoded position
- **Animation Errors**: Skip animation, hide immediately
- **Thread Violations**: Queue updates to main thread