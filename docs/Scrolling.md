# Scrolling with Glide

Glide enables hands-free scrolling on macOS using natural finger movements. Perfect for when your hands are messy from food!

## How It Works

1. **Activate**: Touch your index and middle fingertips together
2. **Scroll**: While touching, move your fingers up or down:
   - **Move down** → Scroll down
   - **Move up** → Scroll up
   - **Move sideways** → Horizontal scroll (if supported by app)
3. **Speed Control**: Faster movement = faster scrolling
4. **Momentum**: Release fingers and scrolling continues with natural deceleration
5. **Stop**: High-five gesture (open palm) for instant stop

## Setup

### Prerequisites
- macOS 10.12 (Sierra) or later
- Python 3.10+
- Accessibility permission granted

### Accessibility Permission

Glide needs Accessibility permission to generate scroll events:

1. Open **System Preferences** → **Security & Privacy** → **Privacy** → **Accessibility**
2. Click the lock icon to make changes
3. Add your Terminal app (or IDE if running from there)
4. Restart Glide

If you see permission errors, double-check this setting.

## Configuration

Edit `glide/io/defaults.yaml` to customize scrolling behavior:

```yaml
scroll:
  enabled: true              # Enable/disable scrolling
  pixels_per_degree: 5.0     # Scroll sensitivity (higher = more responsive)
  max_velocity: 100.0        # Maximum scroll speed in pixels
  respect_system_preference: true  # Honor natural scrolling
  show_hud: true            # Show visual feedback (currently disabled)
```

### Key Settings

- **pixels_per_degree**: Legacy setting (kept for compatibility). The new velocity system uses direct pixel mapping
- **max_velocity**: Maximum scroll speed in pixels per event
- **respect_system_preference**: Follows your macOS natural scrolling setting

## Visual Feedback

When scrolling is triggered, a small HUD appears showing:
- Circular arrow indicating scroll direction
- Fades out automatically after scrolling stops

## Troubleshooting

### No Scrolling
1. Check Accessibility permission is granted
2. Ensure `scroll.enabled: true` in config
3. Verify PyObjC is installed: `pip install -r requirements.txt`

### Scrolling Too Fast/Slow
- Adjust `pixels_per_degree` in config
- Lower values = slower scrolling
- Higher values = faster scrolling

### Wrong Direction
- Toggle `respect_system_preference` in config
- Or change your macOS natural scrolling preference

## Technical Details

- **Velocity-Based Tracking**: Measures fingertip velocity in pixels/second
- **Native Scroll Phases**: Uses proper macOS scroll phases (began → changed → ended)
- **CGEventCreateScrollWheelEvent**: Generates native scroll events with sub-pixel precision
- **Momentum Handoff**: macOS handles momentum scrolling automatically
- **Frame-Rate Independent**: Velocity calculation uses time windows, not frame counts
- **PyObjC Integration**: Direct interface with Quartz Event Services

## Supported Applications

Works with any macOS application that accepts standard scroll events:
- Web browsers (Safari, Chrome, Firefox)
- Document viewers (Preview, PDF Expert)
- Text editors and IDEs
- Most native macOS applications

## Future Improvements

- Visual HUD feedback (currently disabled)
- Per-application sensitivity settings
- Custom gesture mapping
- Two-finger rotation for zoom
- Pinch gestures for zoom control