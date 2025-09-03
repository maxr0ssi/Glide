# Glide API Reference

## Core Components

### Hand Detection

#### `HandLandmarker`
```python
from glide.perception.hands import HandLandmarker

landmarker = HandLandmarker(model_path="models/hand_landmarker.task")
detection = landmarker.detect(image)
```

**Returns**: `HandDetection` with landmarks and confidence score

### Gesture Detection

#### `TouchProofDetector`
```python
from glide.gestures.touchproof import TouchProofDetector

detector = TouchProofDetector(config)
signals = detector.update(landmarks, image, width, height)
```

**Key Properties**:
- `signals.is_touching`: Boolean indicating fingertip contact
- `signals.fused_score`: Combined confidence score (0.0-1.0)
- `signals.proximity_score`: Distance-based score
- `signals.angle_score`: Finger angle convergence score

#### `VelocityTracker`
```python
from glide.gestures.velocity_tracker import VelocityTracker

tracker = VelocityTracker(
    window_ms=100,     # Time window for velocity calculation
    min_samples=3      # Minimum samples for valid velocity
)

velocity = tracker.update(
    index_tip=(x, y),
    middle_tip=(x, y),
    is_touching=True,
    timestamp_ms=now_ms
)
```

**Returns**: `Vec2D` with velocity in pixels/second or None

### Scrolling Integration

#### `VelocityScrollDispatcher`
```python
from glide.runtime.actions.velocity_dispatcher import VelocityScrollDispatcher
from glide.runtime.actions.scroll import ScrollConfig

config = ScrollConfig(
    pixels_per_degree=2.22,
    max_velocity=100.0,
    respect_system_preference=True
)

dispatcher = VelocityScrollDispatcher(config)
dispatcher.dispatch(velocity, state, is_active)
```

## Data Types

### `Vec2D`
```python
@dataclass
class Vec2D:
    x: float                     # X velocity in pixels/second
    y: float                     # Y velocity in pixels/second
    magnitude: float             # Speed in pixels/second
```

### `TouchProofSignals`
```python
@dataclass
class TouchProofSignals:
    proximity_score: float    # Distance-based score
    angle_score: float       # Angle convergence score
    mfc_score: float        # Micro-flow cohesion score
    occlusion_score: float  # Visibility asymmetry score
    fused_score: float      # Combined weighted score
    is_touching: bool       # Final touch state
    debug_state: str        # State machine status
```

### `ScrollConfig`
```python
@dataclass
class ScrollConfig:
    pixels_per_degree: float = 2.22
    max_velocity: float = 100.0
    acceleration_curve: float = 1.5
    respect_system_preference: bool = True
    show_hud: bool = True
    hud_fade_duration_ms: int = 500
```

## Configuration

### AppConfig Structure
```python
from glide.core.config_models import AppConfig

config = AppConfig.from_yaml("glide/io/defaults.yaml")

# Access sub-configurations
config.touchproof    # TouchProof settings
config.scroll        # Scrolling settings
config.kinematics    # Motion tracking settings
```

## Extension Points

### Custom Scroll Actions

Implement continuous scrolling:

```python
from glide.runtime.actions.continuous_scroll import ContinuousScrollAction

class MyCustomScrollAction(ContinuousScrollAction):
    def begin_gesture(self, velocity: Vec2D) -> bool:
        # Start scrolling
        pass
    
    def update_gesture(self, velocity: Vec2D) -> bool:
        # Update scroll velocity
        pass
        
    def end_gesture(self) -> bool:
        # End scrolling, hand off to momentum
        pass
```

### Custom Gestures

1. Create detector in `glide/gestures/`
2. Implement detection logic
3. Return events extending base event types
4. Integrate into main pipeline

## Coordinate Systems

### Hand-Aligned Space
- Origin: Palm center
- X-axis: Wrist to middle finger
- Y-axis: Perpendicular in palm plane
- Scale: Normalized by palm size

### Screen Space
- Standard pixel coordinates
- Origin: Top-left
- Used for raw landmark positions

## Best Practices

1. **Configuration**: Use YAML files for user-adjustable parameters
2. **Normalization**: Always normalize by hand size for scale invariance
3. **Smoothing**: Apply exponential moving average for jittery signals
4. **State Machines**: Use hysteresis to prevent flickering states
5. **Error Handling**: Fail gracefully with sensible defaults