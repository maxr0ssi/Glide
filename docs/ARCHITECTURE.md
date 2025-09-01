# Glide Architecture

## Overview

Glide is a touchless gesture control system that lets you interact with your computer without touching it - perfect for when your hands are messy from food. It uses computer vision to detect when your fingertips touch and tracks circular gestures for scrolling.

## Package Structure

```
glide/
├── app/           # Application entry point
├── core/          # Foundation (types, config models)
├── perception/    # Hand detection via MediaPipe
├── features/      # Feature extraction (alignment, poses)
├── gestures/      # Touch and gesture detection
├── io/            # Configuration and event output
└── ui/            # Visual overlay and display
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
- **Circular**: Detects clockwise and counter-clockwise circular gestures
  - Cumulative angle tracking
  - Speed and direction consistency checks
  - Configurable angle thresholds

### 4. **Application Layer** (`app/`)
- **Main**: Primary application entry point and processing loop
- Orchestrates perception, feature extraction, and gesture detection

### 5. **Configuration & I/O** (`io/`)
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
                                            Circular Detector
                                                    ↓
                                            Event Output → JSON
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
  angle_enter_deg: 20.0
  fused_enter_threshold: 0.80
  
# Circular gestures  
circular:
  min_angle_deg: 90.0
  min_speed: 1.5
```

Pydantic models in `core/config_models.py` provide validation.

## Future Extensibility

The architecture supports:
- Additional gesture types (e.g., pinch, swipe)
- Alternative hand detection backends
- Multiple camera sources
- Network streaming of events
- Improved TouchProof algorithms (see TOUCHPROOF_IMPROVEMENTS.md)
- Multi-hand tracking