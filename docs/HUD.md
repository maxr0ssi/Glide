# Glide HUD - Native macOS Heads-Up Display

The Glide HUD is a native macOS application that provides visual feedback for gesture control without interfering with your workflow.

## Architecture Overview

The HUD system consists of two main components:

1. **Python Backend** - Handles gesture detection and broadcasts events via WebSocket
2. **Swift Frontend** - Native macOS app that displays the HUD overlay

## Features

### Display Modes

- **Minimized Mode (300x150px)**
  - Direction arrows indicate scroll direction
  - Speed bars show scroll velocity
  - Auto-hides after 2 seconds of inactivity
  - Minimal CPU usage

- **Expanded Mode (500x400px)** 
  - Everything from minimized mode
  - Live camera feed with hand tracking overlay
  - TouchProof status indicator
  - Stays visible (no auto-hide)
  - Camera frames throttled to maintain performance

### Visual Design

The HUD features a "liquid nitrogen ice" aesthetic:
- Translucent white glass appearance
- Frost effects and crystalline borders
- Ice particle animations during scrolling
- Cyan glow when TouchProof is active

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

// Camera frame (expanded mode only)
{
  "type": "camera",
  "frame": "<base64-jpeg>",
  "width": 320,
  "height": 240
}

// Initial configuration
{
  "type": "config",
  "position": "bottom-right",
  "opacity": 0.85
}
```

The Swift HUD can send:
```json
// Mode change notification
{
  "type": "mode",
  "expanded": true
}
```

### Performance Optimizations

1. **Camera Streaming**
   - Only sent when HUD is in expanded mode
   - Frames throttled to ~20 FPS
   - JPEG compression at 50% quality
   - Resolution reduced to 320px width

2. **Event Throttling**
   - Scroll events: 60 Hz maximum
   - Camera frames: 30 Hz maximum (effective ~20 FPS)
   - TouchProof: Only on state changes

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