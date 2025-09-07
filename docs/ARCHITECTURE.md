# Glide Architecture

## Overview

Glide is a touchless gesture control system that lets you interact with your computer without touching it - perfect for when your hands are messy from food. It uses computer vision to detect when your fingertips touch and tracks their velocity for natural scrolling.

## Package Structure

```
glide/
├── app/           # Application entry point
├── core/          # Foundation (types, config models)
├── perception/    # Hand detection via MediaPipe
├── features/      # Feature extraction (alignment, poses)
├── gestures/      # Touch and gesture detection
├── runtime/       # Platform-specific action implementations
│   ├── actions/   # Scroll actions and dispatching
│   ├── hud/       # Legacy HUD components
│   └── ipc/       # WebSocket communication
├── io/            # Configuration and event output
└── dev/           # Development-only tools
    └── preview/   # Debug visualization

apps/
└── hud-macos/     # Native macOS HUD application
```

## Core Components

### 1. **Perception Layer** (`perception/`)
- **HandLandmarker**: MediaPipe wrapper for 21-point hand landmark detection
- Uses task-based API with hand_landmarker.task model
- Configurable detection confidence thresholds

### 2. **Feature Extraction** (`features/`)
- **HandAligner**: Transforms coordinates to hand-aligned space (scale/rotation invariant)
- **KinematicsTracker**: Tracks fingertip motion with exponential moving average smoothing
- **FingerPose**: Simple pose detection (open palm, pointing index, two fingers up)

### 3. **Gesture Detection** (`gestures/`)
- **TouchProof**: Multi-signal fusion for fingertip contact detection
  - Proximity-based distance measurement
  - Angle convergence analysis
  - Micro-Flow Cohesion (MFC) for motion coherence
  - Distance-aware adaptive weighting
- **VelocityTracker**: Tracks fingertip velocity in pixels/second
  - Frame-rate independent velocity calculation
  - Time-windowed position sampling
  - Smooth velocity transitions

### 4. **Runtime Layer** (`runtime/`)
- **VelocityScrollDispatcher**: Routes velocity data to platform-specific actions
- **ContinuousScrollAction**: macOS implementation using scroll phases
- **WebSocketBroadcaster** (`ipc/ws.py`): Local WebSocket server for HUD communication
  - Broadcasts scroll events, TouchProof status, and camera frames
  - Throttled event streaming (configurable 30-120 Hz)
  - Session token authentication
  - Localhost-only for security

### 5. **Native HUD** (`apps/hud-macos/`)
- **Swift macOS Application**: Floating heads-up display
  - NSPanel with CMD+CTRL+G hotkey activation
  - Two modes: minimized (300x150) and expanded (500x400)
  - Live camera feed with hand tracking overlay (expanded mode)
  - "Liquid nitrogen ice" aesthetic with translucent effects
  - WebSocket client for real-time updates

### 6. **Application Layer** (`app/`)
- **Main**: Primary application entry point and processing loop
- Orchestrates perception, feature extraction, and gesture detection
- Integrates runtime actions for platform functionality

### 7. **Configuration & I/O** (`io/`)
- **defaults.yaml**: YAML-based configuration with sensible defaults
- **event_output**: JSON event streaming to stdout
- **replay**: Record and replay sessions for testing

## Key Design Principles

### 1. **Type Safety**
Strong typing with Pydantic models and dataclasses:
```python
@dataclass
class TouchProofSignals:
    proximity_score: float
    angle_score: float
    mfc_score: float
    fused_score: float
    is_touching: bool
```

### 2. **Scale Invariance**
All measurements normalized by hand size:
- Distances normalized by finger length
- Coordinates in hand-aligned space
- Adaptive thresholds based on apparent hand size

### 3. **Multi-Signal Fusion**
TouchProof combines complementary signals:
- **Proximity**: Normalized fingertip distance (by finger length)
- **Angle**: Convergence angle between finger directions
- **MFC**: Optical flow coherence between fingertips
- **Visibility**: Landmark visibility/occlusion detection

### 4. **Modular Design**
- Clear separation between touch detection and gesture recognition
- Configuration-driven behavior via YAML
- Easy to add new gesture types

## Data Flow

```
Camera → Frame → HandDetector → Landmarks → HandAligner → Features
                                                    ↓
                                            TouchProof Detector
                                                    ↓
                                            Velocity Tracker
                                                    ↓
                                            Velocity-based Scrolling
                                                    ↓
                        ┌───────────────────┴───────────────────┐
                        │                                       │
                  Event Output → JSON            VelocityScrollDispatcher
                                                        │
                                                Platform Action
                                                (e.g., scroll)
                                                        │
                                                WebSocket Broadcaster
                                                        │
                                    ┌───────────────────┴───────────────────┐
                                    │                                       │
                              Scroll Events                          Camera Frames
                              TouchProof Status                    (Expanded Mode Only)
                                    │                                       │
                                    └───────────────┬───────────────────┘
                                                    │
                                              Native HUD (macOS)
                                              - Visual Feedback
                                              - Camera Preview
                                              - TouchProof Indicator
```

## Performance Characteristics

- **Latency**: <10ms per frame on CPU
- **Frame Rate**: 30+ FPS on modern hardware
- **Touch Detection**: Multi-signal fusion for robust detection
- **CPU Usage**: ~20-30% single core with preview window

## Configuration

The system loads configuration from `glide/io/defaults.yaml`:

```yaml
# TouchProof detection
touchproof:
  proximity_enter: 0.25
  angle_enter_deg: 24.0
  fused_enter_threshold: 0.75
  mfc_window_frames: 5

# Scrolling
scroll:
  enabled: true
  pixels_per_degree: 5.0
  respect_system_preference: true
  # WebSocket HUD
  hud_enabled: true
  hud_ws_port: 8765
  hud_throttle_hz: 60
  camera_throttle_hz: 30
  camera_frame_skip: 3

# Optical flow
optical_flow:
  window_frames: 5
  patch_size: 15
```

Pydantic models in `core/config_models.py` provide validation.

## Future Extensibility

The architecture supports:
- Additional gesture types (e.g., pinch, swipe)
- Cross-platform action implementations (Windows, Linux)
- Alternative hand detection backends
- Multiple camera sources
- Network streaming of events
- Improved TouchProof algorithms
- Multi-hand tracking
