# Glide HUD - Native macOS App

A native macOS HUD (Heads-Up Display) for Glide that shows camera feed with hand tracking overlays and scroll feedback in a unified floating panel.

*quick caveat* I have done one swift project and that was about 3/4 years ago.... So bar the basic syntax, a lot of the swift code is "vibe coded" --> now I do have clear design docs and plans etc... and long conversations but yeah the actual typing of code is about 90% AI.

## Features

### Two Display Modes

1. **Minimized Mode** (300x150px)
   - Direction arrows showing scroll direction
   - Speed bars indicating scroll velocity
   - No camera feed (saves CPU)

2. **Expanded Mode** (500x400px)
   - Everything from minimized mode
   - Live camera feed with hand tracking overlays
   - TouchProof status indicator
   - Camera frames throttled to ~10 FPS for performance

### Visual Design
- "Liquid nitrogen ice" aesthetic
- Translucent white glass appearance
- Frost effects and ice particle animations
- Cyan glow when TouchProof is active

### Controls
- **CMD+CTRL+G**: Toggle HUD visibility
- **Expand button (⤢)**: Switch between minimized/expanded modes
- Auto-hides after 2 seconds of no activity

## Running the HUD

### Quick Start (Integrated Mode)
From the Glide root directory:
```bash
./test_integrated_hud.sh
```

This starts both the Python backend (headless) and the Swift HUD.

### Manual Start

1. Start the Python backend (headless mode):
```bash
python -m glide.app.main --headless
```

2. In another terminal, start the HUD:
```bash
cd apps/hud-macos
swift run
```

### Development Mode

For development with live reload:
```bash
cd apps/hud-macos
swift build && swift run
```

## Architecture

### WebSocket Communication
- Connects to `ws://127.0.0.1:8765/hud`
- Receives events:
  - `scroll`: Velocity and speed updates
  - `hide`: Hide HUD command
  - `config`: Initial configuration
  - `camera`: JPEG-compressed camera frames (expanded mode only)
  - `touchproof`: TouchProof state and hands count
- Sends events:
  - `mode`: Notifies backend when switching between minimized/expanded

### Performance Optimizations
- Camera frames only sent when HUD is in expanded mode
- Frames throttled to ~10 FPS, JPEG compressed
- Scroll events at 30-60 Hz
- Thread-safe UI updates

## Building

Requirements:
- macOS 12.0+
- Swift 5.5+
- Xcode Command Line Tools

Build:
```bash
swift build
```

Run:
```bash
swift run
```

## Troubleshooting

### HUD doesn't appear
- Make sure Python backend is running first
- Check if port 8765 is available
- Grant accessibility permissions for global hotkey

### Camera not showing
- Click expand button to switch to expanded mode
- Check if Python backend has camera permissions
- Verify WebSocket connection in console logs

### Performance issues
- Camera streaming increases CPU usage
- Use minimized mode when camera not needed
- Check Activity Monitor for resource usage
