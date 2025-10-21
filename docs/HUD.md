# Glide HUD - Pulse Ring Indicator

The Glide HUD is a minimal macOS indicator that provides subtle visual feedback for gesture control without interfering with your workflow.

## Architecture Overview

The HUD system consists of two main components:

1. **Python Backend** - Handles gesture detection and broadcasts events via WebSocket
2. **Swift Frontend** - Native macOS app that displays the Pulse Ring indicator

## Features

### Pulse Ring Design

- **Minimal 32x32px indicator**
  - Positioned in top-right corner (20px margins)
  - 5 distinct states with smooth animations
  - Context menu for quick settings
  - Hover interactions

### Visual States

The Pulse Ring has 5 distinct states:
- **Idle**: Subtle breathing pulse (0.6-0.8 opacity)
- **Active**: Bright cyan ring when TouchProof is engaged
- **Scrolling Up**: Upward arrow animation
- **Scrolling Down**: Downward arrow animation
- **Hidden**: Completely faded out

## Technical Implementation

### WebSocket Communication

The Python backend broadcasts events to `ws://127.0.0.1:8765/hud`:

```json
// Scroll event
{
  "type": "scroll",
  "vy": -0.5,      // Vertical velocity
  "speed": 0.25    // Normalized speed (0-1)
}

// Hide event
{
  "type": "hide"
}

// TouchProof status
{
  "type": "touchproof",
  "active": true,
  "hands": 2
}
```

### Performance Optimizations

1. **Minimal Resource Usage**
   - 32x32px indicator uses minimal GPU resources
   - CAShapeLayer for efficient rendering
   - Hardware-accelerated animations

2. **Event Throttling**
   - Scroll events: 60 Hz maximum
   - TouchProof: Only on state changes
   - Auto-hide after 2 seconds of inactivity

3. **Thread Safety**
   - All UI updates wrapped in `DispatchQueue.main.async`
   - WebSocket runs in background thread
   - Async message broadcasting

## Building and Running

### Prerequisites

- macOS 12.0+
- Swift 5.5+
- Xcode Command Line Tools

### Build

```bash
cd apps/hud-macos
swift build
```

### Run

Option 1: With Python backend
```bash
# Terminal 1
python -m glide.app.main --headless

# Terminal 2
cd apps/hud-macos && swift run
```

Option 2: Test script (starts both)
```bash
./scripts/run_with_hud.sh
```

## Controls

- **CMD+CTRL+G** - Toggle HUD visibility
- **Click expand button (⤢)** - Switch to expanded mode
- **Click collapse button (⤡)** - Switch to minimized mode

## Configuration

The HUD respects configuration from the Python backend:

```yaml
# In glide/io/defaults.yaml
scroll:
  hud_enabled: true
  hud_ws_port: 8765
  hud_throttle_hz: 60
  hud_position: "bottom-right"
  hud_opacity: 0.85
```

## Troubleshooting

### HUD doesn't appear
- Ensure Python backend is running first
- Check port 8765 is available
- Grant Accessibility permissions for global hotkey

### Camera not showing
- Click expand button to switch modes
- Check camera permissions for Python
- Verify WebSocket connection in logs

### Performance issues
- Use minimized mode when camera not needed
- Check Activity Monitor for CPU usage
- Ensure no other apps using port 8765

## Future Improvements

- [ ] Customizable hotkey
- [ ] More position options
- [ ] Theme customization
- [ ] Multi-monitor support
- [ ] Settings persistence
