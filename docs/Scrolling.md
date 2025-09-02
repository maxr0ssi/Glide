# Scrolling with Glide

Glide enables hands-free scrolling on macOS using circular gestures. Perfect for when your hands are messy from food!

## How It Works

1. **Activate**: Touch your index and middle fingertips together
2. **Scroll**: While touching, make circular motions:
   - **Clockwise** circles → Scroll down
   - **Counter-clockwise** circles → Scroll up
3. **Speed Control**: Larger circles = faster scrolling

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
  pixels_per_degree: 2.22    # Scroll speed (higher = faster)
  max_velocity: 100.0        # Maximum scroll speed
  respect_system_preference: true  # Honor natural scrolling
  show_hud: true            # Show visual feedback
```

### Key Settings

- **pixels_per_degree**: Controls scroll sensitivity. Default maps 180° rotation to 400 pixels
- **max_velocity**: Prevents extremely fast scrolling from large gestures
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

- Uses PyObjC to interface with macOS Quartz Event Services
- Generates native `CGScrollWheelEvent` events
- Respects system natural scrolling preference
- Thread-safe HUD implementation using tkinter

## Supported Applications

Works with any macOS application that accepts standard scroll events:
- Web browsers (Safari, Chrome, Firefox)
- Document viewers (Preview, PDF Expert)
- Text editors and IDEs
- Most native macOS applications

## Future Improvements

- Momentum scrolling
- Horizontal scrolling support
- Per-application sensitivity settings
- Gesture customization