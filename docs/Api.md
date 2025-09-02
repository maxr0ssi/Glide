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

#### `CircularDetector`
```python
from glide.gestures.circular import CircularDetector, CircularEvent

detector = CircularDetector(
    min_angle_deg=90.0,
    max_angle_deg=720.0,
    min_speed=1.5
)

result = detector.update(trail, finger_length, is_touching, timestamp_ms)
```

**Returns**: `CircularDetection` with optional `CircularEvent`

### Scrolling Integration

#### `ScrollDispatcher`
```python
from glide.runtime.actions.scroll import ScrollDispatcher, ScrollConfig

config = ScrollConfig(
    pixels_per_degree=2.22,
    max_velocity=100.0,
    respect_system_preference=True
)

dispatcher = ScrollDispatcher(config)
success = dispatcher.dispatch(circular_event)
```

## Data Types

### `CircularEvent`
```python
@dataclass
class CircularEvent:
    ts_ms: int                    # Timestamp in milliseconds
    direction: CircularDirection  # CLOCKWISE or COUNTER_CLOCKWISE
    total_angle_deg: float       # Total rotation angle
    strength: float              # Gesture confidence (0.0-1.0)
    duration_ms: int             # Gesture duration
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
config.circular      # Circular gesture settings
config.scroll        # Scrolling settings
```

## Extension Points

### Custom Scroll Actions

Implement the `ScrollAction` protocol:

```python
from glide.runtime.actions.scroll import ScrollAction

class MyCustomScrollAction(ScrollAction):
    def execute(self, event: CircularEvent) -> None:
        # Your implementation
        pass
    
    def cancel(self) -> None:
        # Cancel ongoing scrolls
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