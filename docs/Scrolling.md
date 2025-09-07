# Scrolling with Glide

Glide enables hands-free scrolling on macOS using natural finger movements. Perfect for when your hands are messy from food!

## How It Works

1. **Activate**: Touch your index and middle fingertips together
2. **Scroll**: While touching, move your fingers up or down:
   - **Move down** → Scroll down
   - **Move up** → Scroll up
   - **Move faster** → Scroll faster
3. **Speed Control**: Direct velocity mapping - your finger speed controls scroll speed
4. **Momentum**: Release fingers and macOS handles natural deceleration
5. **Stop**: High-five gesture (open palm) for instant stop

## Visual Feedback

When scrolling is enabled with HUD support, you'll see:
- **Native HUD** (CMD+CTRL+G to toggle):
  - Minimized mode: Direction arrows and speed bars
  - Expanded mode: Live camera feed with hand tracking
- TouchProof indicator glows cyan when fingers are touching

## Setup

### Prerequisites
- macOS 12.0 (Monterey) or later
- Python 3.10+
- Swift 5.5+ (for HUD)
- Accessibility permission granted

### Accessibility Permission

Glide needs Accessibility permission to generate scroll events:

1. Open **System Preferences** → **Security & Privacy** → **Privacy** → **Accessibility**
2. Click the lock icon to make changes
3. Add your Terminal app (or IDE if running from there)
4. For HUD: Also add the GlideHUD app
5. Restart Glide

If you see permission errors, double-check this setting.

### Camera Permission

For the HUD camera preview:
1. Open **System Preferences** → **Security & Privacy** → **Privacy** → **Camera**
2. Grant permission to Python/Terminal

## Configuration

Edit `glide/io/defaults.yaml` to customize scrolling behavior:

```yaml
scroll:
  enabled: true              # Enable/disable scrolling
  pixels_per_degree: 5.0     # Scroll sensitivity (higher = more responsive)
  max_velocity: 100.0        # Maximum scroll speed in pixels
  respect_system_preference: true  # Honor natural scrolling
  
  # HUD configuration
  hud_enabled: true          # Enable WebSocket HUD
  hud_ws_port: 8765         # WebSocket port
  hud_throttle_hz: 60       # Event update rate
  camera_throttle_hz: 30    # Camera frame rate
  camera_frame_skip: 3      # Only send every Nth frame
```

## Technical Implementation

### Velocity-Based System

Glide uses a modern velocity-based scrolling approach:

1. **VelocityTracker** tracks fingertip positions over a 100ms window
2. **Direct velocity mapping** - finger speed in pixels/second → scroll speed
3. **Native scroll phases** - proper macOS integration with:
   - `kCGScrollPhaseBegan` - When fingers touch
   - `kCGScrollPhaseChanged` - During movement
   - `kCGScrollPhaseEnded` - When fingers release
4. **macOS momentum** - The OS handles deceleration naturally

### Key Improvements over Legacy Systems

- **No angle accumulation** - Direct velocity measurement
- **Frame-rate independent** - Consistent at any FPS
- **Simple state machine** - Just IDLE → SCROLLING
- **Native feel** - Leverages macOS scroll acceleration curves
- **Sub-pixel precision** - Smooth scrolling at any speed

### Architecture Components

- `glide/gestures/velocity_tracker.py` - Velocity calculation with EMA smoothing
- `glide/gestures/velocity_controller.py` - State management
- `glide/runtime/actions/continuous_scroll.py` - macOS event generation
- `glide/runtime/actions/velocity_dispatcher.py` - Gesture lifecycle
- `glide/runtime/ipc/ws.py` - WebSocket broadcaster for HUD
- `apps/hud-macos/` - Native Swift HUD application

## Troubleshooting

### Scrolling not working
- Check Accessibility permission
- Ensure `scroll.enabled: true` in config
- Try running with `--debug` flag

### HUD not appearing
- Press CMD+CTRL+G to toggle
- Check port 8765 is available
- Ensure Python backend is running first

### Jerky scrolling
- Adjust `pixels_per_degree` (try 3.0-7.0)
- Check camera FPS (should be 30+)
- Close other CPU-intensive apps

### Wrong scroll direction
- Toggle `respect_system_preference` in config
- Or change Natural Scrolling in System Preferences

## Performance

- **Latency**: <10ms from movement to scroll event
- **CPU Usage**: ~20-30% with HUD in expanded mode
- **Frame Rate**: 30+ FPS hand tracking
- **Memory**: ~100MB Python + ~50MB HUD