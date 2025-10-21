# Glide - Touch-Free Gesture Control for macOS

> *Because greasy fingers and MacBooks don't mix.*

I built Glide to solve a simple problem: I wanted to scroll through articles while eating lunch without getting my keyboard dirty. What started as a weekend hack evolved into a sophisticated gesture recognition system using computer vision and multi-signal sensor fusion.

![Glide Demo](docs/assets/glide-demo.gif)

## 🎯 What It Does

Glide lets you control your Mac with simple hand gestures - no touching required. Just pinch your fingers together and move them up or down to scroll. It's like having a touchpad in thin air.

**Key Features:**
- **Touch-Free Scrolling** - Connect index + middle finger, move up/down to scroll
- **Minimal UI** - Tiny 32px pulse ring indicator that stays out of your way
- **Real-Time Performance** - 60 FPS gesture tracking with < 50ms latency
- **Smart Detection** - Multi-signal fusion prevents false positives

## 🚀 Quick Start

```bash
# One-time setup
git clone https://github.com/maxr0ssi/Glide.git
cd Glide
make setup

# Run it
make run

# That's it! Press CMD+CTRL+G to toggle the HUD
```

## 💡 Technical Highlights

### TouchProof™ Technology
I developed a multi-signal fusion algorithm that combines three independent signals to detect when fingertips actually touch:

```python
# Simplified version of the TouchProof algorithm
proximity = normalized_distance(index_tip, middle_tip)
angle = finger_convergence_angle(index, middle)
mfc = optical_flow_coherence(index_tip, middle_tip)

touch_confidence = weighted_fusion(proximity, angle, mfc)
```

This approach reduces false positives by 85% compared to simple distance thresholding.

### Pulse Ring HUD
Instead of a clunky overlay, I designed a minimal 32x32px indicator that communicates everything through a single animated ring:

```
◯ - Idle (dim white, 20% opacity)
◉ - Active (cyan pulse, breathing animation)
◉↑ - Scrolling up
◉↓ - Scrolling down
```

The entire HUD is just ~400 lines of Swift using CAShapeLayer for buttery-smooth GPU-accelerated animations.

### Real-Time Pipeline
```
Camera (720p @60fps)
    ↓
MediaPipe Hand Detection (21 landmarks)
    ↓
TouchProof Signal Processing
    ↓
Velocity-Based Scroll Mapping
    ↓
Native macOS CGEvent Generation
    ↓
WebSocket → Pulse Ring HUD
```

## 🏗️ Architecture

Glide uses a modular architecture that separates concerns cleanly:

```
glide/
├── perception/     # Computer vision (MediaPipe wrapper)
├── gestures/       # Gesture detection algorithms
│   ├── touchproof.py       # Multi-signal fusion
│   └── velocity_tracker.py # Movement → scroll mapping
├── runtime/        # Event dispatch & IPC
│   └── ipc/ws.py  # WebSocket for HUD communication
└── app/           # Application entry point

apps/hud-macos/    # Native Swift HUD
├── PulseRingWindow.swift  # 32x32 transparent window
└── PulseRingView.swift    # Ring animation logic
```

## 🔧 Key Engineering Decisions

1. **Why MediaPipe?** - Best-in-class hand tracking with minimal latency. The model runs at 15ms/frame on M1.

2. **Why WebSocket for IPC?** - Clean separation between Python CV backend and Swift UI. Allows for future web/mobile HUDs.

3. **Why Velocity-Based Scrolling?** - Maps naturally to how we think about scrolling. Integrates perfectly with macOS momentum scrolling.

4. **Why Such a Minimal HUD?** - Less is more. The 32px ring provides all necessary feedback without cluttering the screen.

## 📊 Performance

- **Latency**: < 50ms from gesture to scroll event
- **CPU Usage**: ~8% on M1 MacBook Air
- **Memory**: 120MB (includes MediaPipe model)
- **Battery Impact**: Negligible in daily use

## 🛠️ Installation

### Requirements
- macOS 12+ (uses modern CGEvent APIs)
- Python 3.10+
- Webcam
- Swift 5.5+ (for HUD)

### Setup
```bash
# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download MediaPipe models
python setup_models.py

# Grant accessibility permissions
# System Preferences > Security & Privacy > Accessibility > Terminal ✓
```

## 🎮 Usage

### Basic Controls
1. **Activate**: Touch index + middle fingertips together
2. **Scroll**: Move connected fingers up/down
3. **Speed**: Move faster = scroll faster
4. **Stop**: Release fingers or high-five gesture

### HUD Controls
- `CMD+CTRL+G` - Toggle HUD visibility
- Right-click ring - Position & visibility options
- Hover → × button - Hide permanently

### Advanced Options
```bash
# Run headless (no preview window)
python -m glide.app.main --headless
```

## 🔬 Technical Deep Dive

### Multi-Signal Fusion
The TouchProof algorithm prevents false positives by combining:
- **Proximity Signal**: Euclidean distance normalized by hand size
- **Angle Signal**: Finger convergence angle (parallel = touching)
- **MFC Signal**: Optical flow coherence between fingertips

### Velocity Mapping
Instead of position-based scrolling, Glide uses velocity:
```python
velocity = exponential_smooth(finger_movement)
scroll_pixels = velocity * sensitivity * frame_time
```

This feels more natural and works seamlessly with macOS momentum.

## 🚧 Future Improvements

- [ ] Multi-hand support for zooming/rotating
- [ ] Multi-hand support for starting and stopping videos
- [ ] Custom gesture recording & playback
- [ ] ML model fine-tuning for specific users
- [ ] Cross-platform support (Windows/Linux)
- [ ] Browser extension for web-specific gestures

## 📄 License

MIT - Use it, modify it, learn from it!

## 📬 Contact

Built by Max Rossi - [LinkedIn](https://linkedin.com/in/maxr0ssi) |

---

*P.S. - Yes, I did eat an entire burrito while testing this.*
