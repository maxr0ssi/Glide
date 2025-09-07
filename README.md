# Glide - Touchless Gesture Control

I like eating while reading or watching videos. My laptop is less keen. Keyboards and burger bun grease are not a power couple. So I am building Glide, a small, fun and stupid solution to use my screen without touching it.
(plus it looks rather cool in lectures flicking through slides)
Connect your index and middle finger to activate. Then move them up or down to scroll. Keep the crumbs on your plate and the smears off your kit.

## Features

- **TouchProof Technology** - Multi-signal fusion for detecting when fingertips touch
- **MediaPipe Hand Tracking** - Accurate 21-point hand landmark detection  
- **Velocity-Based Scrolling** - Natural movement-driven scrolling
- **Real-time Visual Feedback** - Live preview with touch status and signal visualization
- **Native macOS HUD** - Beautiful floating heads-up display with camera feed integration
- **Modular Architecture** - Clean separation of detection, visualization, and output

## Requirements

- Python 3.10+
- Webcam
- macOS (for scrolling feature)
- Swift 5.5+ and Xcode Command Line Tools (for HUD)

## Installation

```bash
# Create virtual environment with Python 3.10
python3.10 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Set up MediaPipe model files
python setup_models.py
```

### macOS Scrolling Setup

To enable scrolling on macOS, you need to grant Accessibility permission:

1. Go to **System Preferences** > **Security & Privacy** > **Privacy** > **Accessibility**
2. Click the lock to make changes
3. Add your Terminal app (or IDE if running from there)
4. Restart the Glide application

The scrolling feature uses PyObjC to generate native scroll events.

### Building the Native HUD (Optional)

Glide includes a (not-so) beautiful native macOS HUD that shows scroll feedback and camera feed:

```bash
cd apps/hud-macos
swift build
```

## Usage

```bash
python -m glide.app.main --model models/hand_landmarker.task
```

### Options

- `--config PATH` - Path to config file (default: `config/config.yaml`)
- `--model PATH` - Path to MediaPipe model (default: auto-detect)
- `--headless` - Run without preview window (recommended with HUD)
- `--no-hud` - Disable WebSocket HUD broadcaster
- `--hud-port PORT` - WebSocket port for HUD (default: 8765)
- `--record PATH` - Record events to JSONL file
- `--debug` - Enable debug output

### Controls

- **Touch Detection**: Connect your index and middle fingertips to activate
- **Smooth Scrolling**: Natural velocity-based scrolling:
  - **Move fingers up/down** → Scroll in that direction
  - **Move faster** → Scroll faster
  - **Release** → macOS momentum takes over
  - **High-five gesture** → Instant stop
- **Exit**: Press 'q' or ESC to quit

Preview window shows:
- Touch detection status (green/red circle)
- Signal strength bars
- Detected gestures
- Hand landmarks
- FPS counter

### Native HUD (macOS)

The native HUD provides a floating display that:
- **Minimized Mode**: Shows direction arrows and speed bars
- **Expanded Mode**: Adds live camera feed with hand tracking overlay
- Press `CMD+CTRL+G` to toggle HUD visibility
- Click expand button (⤢) to switch modes
- Auto-hides in minimized mode, stays visible in expanded mode

To run with HUD:
```bash
# Terminal 1: Start backend in headless mode
python -m glide.app.main --headless

# Terminal 2: Start HUD
cd apps/hud-macos && swift run
```

## How It Works

### TouchProof Detection
The system uses three complementary signals to detect fingertip contact:

1. **Proximity** - Normalized distance between fingertips
2. **Angle** - Convergence angle of fingers
3. **MFC (Micro-Flow Cohesion)** - Optical flow coherence between fingertips

### Gesture Recognition
- **Touch Detection** - Pinch index and middle fingertips together to activate
- **Velocity-Based Scrolling** - Direct finger movement controls scroll speed
- **Native Momentum** - macOS handles deceleration naturally
- **Gesture Controls** - High-five to stop instantly

## Project Structure

```
Glide/
├── glide/
│   ├── app/             # Application entry points
│   │   └── main.py      # Main application
│   ├── core/            # Core utilities and types
│   │   ├── types.py     # Data structures and configuration
│   │   └── config_models.py  # Configuration models
│   ├── perception/      # Input processing
│   │   └── hands.py     # MediaPipe hand detection
│   ├── gestures/        # Gesture detection
│   │   ├── touchproof.py    # Multi-signal fingertip touch detection
│   │   ├── velocity_tracker.py  # Velocity-based scrolling
│   │   └── velocity_controller.py  # Scroll state management
│   ├── features/        # Feature extraction
│   │   ├── kinematics.py    # Motion tracking
│   │   └── poses.py         # Hand pose classification
│   ├── runtime/         # Runtime components
│   │   ├── actions/     # Gesture actions
│   │   │   └── velocity_dispatcher.py  # Scroll event dispatcher
│   │   └── ipc/         # Inter-process communication
│   │       └── ws.py    # WebSocket broadcaster for HUD
│   └── io/              # Input/output
│       └── defaults.yaml    # Default configuration
├── apps/
│   └── hud-macos/       # Native macOS HUD
│       ├── Sources/     # Swift source code
│       └── Package.swift # Swift package manifest
├── models/              # MediaPipe models
├── docs/                # Documentation
└── requirements.txt     # Python dependencies
```

## Configuration

Edit `glide/io/defaults.yaml` to customize:

```yaml
# TouchProof detection
touchproof:
  proximity_enter: 0.25      # Normalized distance to trigger
  angle_enter_deg: 20.0      # Max angle for parallel fingers
  fused_enter_threshold: 0.80  # Fused score to trigger touch
  
# Circular gesture detection  
circular:
  min_angle_deg: 90.0        # Minimum angle to trigger
  min_speed: 1.5             # Minimum speed to start
  cooldown_ms: 500           # Pause between gestures
```

## Output Format

Detected gestures are output as JSON:

```json
{
  "type": "circular",
  "direction": "clockwise",
  "angle_deg": 180.5,
  "duration_ms": 450,
  "timestamp": 1735689600000
}
```

## Architecture

```
Camera Input
     ↓
MediaPipe Hand Detection
     ↓
Coordinate Normalization
     ↓
┌─────────────┬──────────────┐
│ Touch       │ Gesture      │
│ Detection   │ Detection    │
│ (TouchProof)│ (Kinematics) │
└─────────────┴──────────────┘
     ↓
Event Arbitration
     ↓
JSON Output + Visualization
```