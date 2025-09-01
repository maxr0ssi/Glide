# Glide - Touchless Gesture Control

I like eating while reading or watching videos. My laptop is less keen. Keyboards and burger bun grease are not a power couple. So I am building Glide, a small, fun and stupid solution to use my screen about without touching it.
(plus it looks rather cool in lectures flicking through slides)
Conenct your index and middle finger to activate. Then trace a tidy little circle to scroll. Keep the crumbs on your plate and the smears off your kit.

## Features

- **TouchProof Technology** - Multi-signal fusion for detecting when fingertips touch
- **MediaPipe Hand Tracking** - Accurate 21-point hand landmark detection  
- **Circular Gesture Recognition** - Clockwise and counter-clockwise gesture detection
- **Real-time Visual Feedback** - Live preview with touch status and signal visualization
- **Modular Architecture** - Clean separation of detection, visualization, and output

## Requirements

- Python 3.10+
- Webcam

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

## Usage

```bash
python -m glide.app.main --model models/hand_landmarker.task
```

### Options

- `--config PATH` - Path to config file (default: `config/config.yaml`)
- `--model PATH` - Path to MediaPipe model (default: auto-detect)
- `--headless` - Run without preview window
- `--record PATH` - Record events to JSONL file
- `--debug` - Enable debug output

### Controls

- **Q** or **ESC**: Quit
- (temporary) Preview window shows:
  - Touch detection status (green/red circle)
  - Signal strength bars
  - Hand landmarks
  - FPS counter

## How It Works

### TouchProof Detection
The system uses three complementary signals to detect fingertip contact:

1. **Proximity** - Normalized distance between fingertips
2. **Angle** - Convergence angle of fingers
3. **MFC (Micro-Flow Cohesion)** - Optical flow coherence between fingertips

### Gesture Recognition
- **Touch Detection** - Pinch index and middle fingertips together to activate. PREREQUISTE for gestures to reference
- **Circular Gestures** - Make clockwise or counter-clockwise circular motions

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
│   │   ├── circular.py      # Circular gesture recognition
│   │   └── kinematics.py    # Motion tracking
│   ├── features/        # Feature extraction
│   │   ├── alignment.py     # Hand coordinate normalization
│   │   └── fingerpose.py    # Hand pose classification
│   ├── ui/              # Display and visualization
│   │   ├── overlay.py   # UI rendering
│   │   └── utils.py     # Display utilities
│   └── io/              # Input/output
│       ├── event_output.py  # Event streaming
│       └── defaults.yaml    # Default configuration
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