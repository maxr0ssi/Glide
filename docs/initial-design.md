# Glide Technical Design Document

## Overview

Glide is a touchless gesture control system that detects fingertip contact and circular gestures using webcam input. Built for eating while computing - keep your greasy fingers off your devices!

## System Architecture

### High-Level Architecture

```
┌─────────────┐     ┌──────────────┐     ┌────────────────┐     ┌──────────────┐
│   Camera    │────▶│  MediaPipe   │────▶│  Hand Aligner  │────▶│  TouchProof  │
│  Capture    │     │   Hands      │     │                │     │  Detector    │
└─────────────┘     └──────────────┘     └────────────────┘     └──────────────┘
                                                                          │
                                                                          ▼
┌─────────────┐     ┌──────────────┐     ┌────────────────┐     ┌──────────────┐
│   Console   │◀────│   Event      │◀────│    Circular    │◀────│  Kinematics  │
│   Output    │     │  Output      │     │   Detector     │     │   Tracker    │
└─────────────┘     └──────────────┘     └────────────────┘     └──────────────┘
       │
       ▼
┌─────────────┐
│   HUD       │
│  Overlay    │
└─────────────┘
```

### Component Responsibilities

1. **Camera Capture**: Manages webcam access via OpenCV
2. **MediaPipe Hands**: Performs hand detection and 21-point landmark extraction
3. **Hand Aligner**: Normalizes coordinates to hand-aligned space (scale/rotation invariant)
4. **TouchProof Detector**: Multi-signal fusion to detect fingertip contact
5. **Kinematics Tracker**: Tracks finger motion trails with EMA smoothing
6. **Circular Detector**: Analyzes motion patterns for circular gestures
7. **Event Output**: Streams gesture events as JSON to stdout
8. **HUD Overlay**: Renders touch status and signal visualization
9. **Console Output**: JSON event streaming for integration

## Detailed Component Specifications

### 1. Camera Capture Module

```python
class CameraCapture:
    """Manages webcam access and frame acquisition."""
    
    def __init__(self, camera_index: int = 0, frame_width: int = 960):
        """
        Initialize camera capture.
        
        Args:
            camera_index: Camera device index (default: 0)
            frame_width: Target frame width in pixels (default: 960)
        
        Raises:
            CameraError: If camera cannot be initialized
        """
        
    def read_frame(self) -> tuple[bool, np.ndarray]:
        """
        Read a single frame from camera.
        
        Returns:
            success: Whether frame was successfully read
            frame: BGR frame as numpy array (H, W, 3)
        """
        
    def release(self) -> None:
        """Release camera resources."""
```

### 2. Hand Landmark Detection Module

```python
class HandLandmarker:
    """MediaPipe hand detection with 21 landmarks."""
    
    def __init__(self, model_path: str, min_confidence: float = 0.5):
        """
        Initialize MediaPipe hand landmarker.
        
        Args:
            model_path: Path to hand_landmarker.task model
            min_confidence: Minimum detection confidence
        """
        
    def detect(self, rgb_frame: np.ndarray) -> Optional[HandDet]:
        """
        Detect hand landmarks in frame.
        
        Args:
            rgb_frame: RGB frame array
            
        Returns:
            HandDet with landmarks and confidence, or None
        """
```

### 3. TouchProof Detection Module

```python
@dataclass
class TouchProofSignals:
    """Multi-signal touch detection results."""
    proximity_score: float      # 0-1 (closer = higher)
    angle_score: float         # 0-1 (parallel = higher)
    mfc_score: float          # 0-1 (coherent motion = higher)
    distance_factor: float    # 0-1 (0=close, 1=far)
    fused_score: float       # 0-1 overall confidence
    is_touching: bool        # Final decision
    
class TouchProofDetector:
    """Multi-signal fusion for fingertip contact detection."""
    
    def update(self, landmarks: List[Landmark], 
               frame_bgr: np.ndarray,
               width: int, height: int) -> TouchProofSignals:
        """
        Detect fingertip contact using multiple signals.
        
        Args:
            landmarks: Hand landmarks from MediaPipe
            frame_bgr: Current camera frame
            width, height: Frame dimensions
            
        Returns:
            TouchProofSignals with all detection signals
        """
```

### 4. Circular Gesture Detection Module

```python
@dataclass
class CircularEvent:
    """Circular gesture event data."""
    direction: CircularDirection  # CLOCKWISE or COUNTER_CLOCKWISE
    total_angle_deg: float       # Total rotation angle
    duration_ms: int            # Gesture duration
    timestamp: int             # Event timestamp
    
class CircularDetector:
    """Detects circular/arc gestures from finger trails."""
    
    def update(self, trail: Deque[Tuple[float, float]], 
               finger_length: float,
               is_touching: bool,
               ts_now_ms: int) -> CircularDetection:
        """
        Update circular gesture detection.
        
        Args:
            trail: Recent finger positions
            finger_length: For normalization
            is_touching: From TouchProof detector
            ts_now_ms: Current timestamp
            
        Returns:
            CircularDetection with gesture info
        """
```

### 5. Hand Alignment Module

```python
class HandAligner:
    """Transforms coordinates to hand-aligned space."""
    
    def __init__(self):
        """Initialize hand alignment transformer."""
        
    def update(self, landmarks: List[Landmark], 
               width: int, height: int) -> bool:
        """
        Update alignment from new landmarks.
        
        Args:
            landmarks: 21 hand landmarks
            width, height: Frame dimensions
            
        Returns:
            Success status
        """
        
    def get_normalized_distance(self, landmarks: List[Landmark]) -> float:
        """
        Get fingertip distance normalized by finger length.
        
        Returns:
            Distance as fraction of index finger length
        """
        
    def get_fingertip_angle(self, landmarks: List[Landmark]) -> float:
        """
        Get angle between index and middle fingertips.
        
        Returns:
            Angle in degrees (0 = parallel)
        """
```

### 6. Configuration Management

```python
from pydantic import BaseModel, Field

class TouchProofConfig(BaseModel):
    """TouchProof detection configuration."""
    proximity_enter: float = Field(0.25, ge=0.0, le=1.0)
    proximity_exit: float = Field(0.40, ge=0.0, le=1.0)
    angle_enter_deg: float = Field(20.0, ge=0.0, le=90.0)
    angle_exit_deg: float = Field(28.0, ge=0.0, le=90.0)
    fused_enter_threshold: float = Field(0.80, ge=0.0, le=1.0)
    fused_exit_threshold: float = Field(0.60, ge=0.0, le=1.0)
    k_d: float = Field(0.30, description="Distance coefficient")
    k_theta: float = Field(4.0, description="Angle coefficient")
    mfc_window_frames: int = Field(5, ge=1, le=10)
    frames_to_enter: int = Field(3, ge=1, le=10)
    frames_to_exit: int = Field(3, ge=1, le=10)

class CircularConfig(BaseModel):
    """Circular gesture configuration."""
    min_angle_deg: float = Field(90.0, ge=45.0, le=180.0)
    max_angle_deg: float = Field(720.0, ge=180.0, le=1080.0)
    min_speed: float = Field(1.5, ge=0.5, le=5.0)
    exit_speed_factor: float = Field(0.5, ge=0.1, le=0.9)
    max_duration_ms: int = Field(1000, ge=500, le=3000)
    cooldown_ms: int = Field(500, ge=100, le=2000)
    angle_tolerance_deg: float = Field(45.0, ge=15.0, le=90.0)
```

### 7. Event Output Module

```python
class EventOutputStream:
    """Streams gesture events as JSON to stdout."""
    
    def __init__(self):
        """Initialize event output stream."""
        
    def emit_circular(self, event: CircularEvent) -> None:
        """
        Emit circular gesture event.
        
        Output format:
        {
            "type": "circular",
            "direction": "clockwise",
            "angle_deg": 180.5,
            "duration_ms": 450,
            "timestamp": 1735689600000
        }
        """
        
    def emit_touch(self, is_touching: bool, timestamp: int) -> None:
        """
        Emit touch state change event.
        
        Output format:
        {
            "type": "touch",
            "state": "pressed" | "released",
            "timestamp": 1735689600000
        }
        """
```

### 8. HUD Overlay Module

```python
@dataclass
class HUDConfig:
    """HUD display configuration."""
    show_fps: bool = True
    show_landmarks: bool = True
    show_confidence: bool = True
    show_state: bool = True
    fade_duration_ms: int = 600

class HUDOverlay:
    """Renders heads-up display on video frames."""
    
    def __init__(self, config: HUDConfig):
        """Initialize HUD with configuration."""
        
    def render(self,
               frame: np.ndarray,
               fps: float,
               latency_ms: float,
               hand_present: bool,
               state: GestureState,
               last_swipe: Optional[tuple[str, float, int]]) -> np.ndarray:
        """
        Render HUD elements on frame.
        
        Args:
            frame: BGR frame to render on
            fps: Current frames per second
            latency_ms: Processing latency
            hand_present: Whether hand is detected
            state: Current state machine state
            last_swipe: (direction, confidence, timestamp_ms) tuple
            
        Returns:
            Frame with HUD overlay
        """
```

## Data Models

### Core Data Structures

```python
@dataclass
class Config:
    """Application configuration."""
    # Camera settings
    camera_index: int = 0
    frame_width: int = 960
    
    # Detection settings
    buffer_length: int = 20
    lookback_frames: int = 6
    
    # Classification thresholds
    min_norm_displacement: float = 0.85
    dominant_axis_ratio: float = 1.2
    confidence_threshold: float = 0.8
    
    # Timing settings
    cooldown_ms: int = 600
    target_fps: int = 20
    
    # UI settings
    mirror_feed: bool = True
    hud_config: HUDConfig = field(default_factory=HUDConfig)
    
    # Logging settings
    log_level: str = "INFO"
    log_file: Optional[str] = None
    jsonl_output: Optional[str] = None

@dataclass
class PerformanceMetrics:
    """Runtime performance measurements."""
    fps_samples: deque[float]  # Last N FPS measurements
    latency_samples: deque[float]  # Last N latency measurements
    
    @property
    def avg_fps(self) -> float:
        """Moving average FPS."""
        
    @property
    def avg_latency_ms(self) -> float:
        """Moving average latency in milliseconds."""
        
    @property
    def p95_latency_ms(self) -> float:
        """95th percentile latency."""
```

## System Invariants

1. **Single Hand Constraint**: System processes exactly one hand at a time
2. **Touch Requirement**: Circular gestures only detected when fingers are touching
3. **Normalization**: All distances normalized by finger length for scale invariance
4. **Signal Fusion**: TouchProof uses weighted combination of multiple signals
5. **Hysteresis**: State changes require multiple consistent frames
6. **Frame Synchronization**: Timestamps increase monotonically

## Configuration Management

### Configuration Loading

```python
class ConfigLoader:
    """Loads configuration from multiple sources."""
    
    @staticmethod
    def load(config_file: Optional[str] = None,
             cli_args: Optional[dict] = None) -> Config:
        """
        Load configuration with precedence: CLI > file > defaults.
        
        Args:
            config_file: Optional YAML config file path
            cli_args: Optional CLI argument overrides
            
        Returns:
            Merged configuration object
        """
```

### Runtime Adjustments

```python
class RuntimeControls:
    """Handles runtime configuration adjustments."""
    
    def __init__(self, config: Config):
        """Initialize with base configuration."""
        
    def handle_keypress(self, key: str) -> Optional[str]:
        """
        Handle configuration hotkeys.
        
        Args:
            key: Pressed key character
            
        Returns:
            Status message if configuration changed
        """
```

## Error Handling

### Error Types

```python
class GlideError(Exception):
    """Base exception for Glide errors."""

class CameraError(GlideError):
    """Camera initialization or access errors."""

class DetectionError(GlideError):
    """Hand detection errors."""

class ConfigError(GlideError):
    """Configuration validation errors."""
```

### Recovery Strategies

1. **Camera Failures**:
   - Retry with exponential backoff (3 attempts)
   - Fall back to alternate camera index
   - Display error overlay and exit gracefully

2. **Detection Failures**:
   - Reset motion buffer on hand loss
   - Transition to IDLE state
   - Log detection quality metrics

3. **Performance Degradation**:
   - Auto-reduce frame resolution if FPS < 15
   - Skip frames if processing lag exceeds threshold
   - Warn user via HUD

## Performance Optimization

### Frame Processing Pipeline

```python
class FrameProcessor:
    """Optimized frame processing pipeline."""
    
    def __init__(self, config: Config):
        """Initialize processing pipeline."""
        
    async def process_frame(self, 
                           frame: np.ndarray,
                           timestamp_ms: int) -> ProcessingResult:
        """
        Process single frame through pipeline.
        
        Optimizations:
        - Reuse MediaPipe graph between frames
        - Skip redundant color conversions
        - Process at reduced resolution if needed
        """
```

### Performance Monitoring

```python
class PerformanceMonitor:
    """Monitors and reports performance metrics."""
    
    def __init__(self, 
                 sample_window: int = 30,
                 auto_adjust: bool = True):
        """
        Initialize performance monitor.
        
        Args:
            sample_window: Number of samples for moving averages
            auto_adjust: Enable automatic quality adjustments
        """
        
    def update(self, 
               frame_time_ms: float,
               processing_time_ms: float) -> PerformanceAction:
        """
        Update metrics and suggest actions.
        
        Returns:
            Suggested performance action (e.g., reduce resolution)
        """
```

## Testing Strategy

### Unit Test Coverage

1. **Feature Extraction**:
   - Centroid calculation accuracy
   - Hand size normalization
   - Coordinate space conversions

2. **Motion Classification**:
   - Displacement calculations
   - Axis dominance detection
   - Confidence scoring

3. **State Machine**:
   - Valid state transitions
   - Cooldown timing
   - Edge case handling

### Integration Tests

```python
class SwipeTestHarness:
    """Test harness for swipe detection validation."""
    
    def replay_trace(self, 
                     trace_file: str,
                     expected_events: list[GestureEvent]) -> TestResult:
        """
        Replay recorded motion trace and validate events.
        
        Args:
            trace_file: Path to recorded trace file
            expected_events: Expected gesture events
            
        Returns:
            Test result with pass/fail and diagnostics
        """
```

### Performance Benchmarks

1. **Latency Test**: Measure capture-to-output timing
2. **Throughput Test**: Verify sustained 20+ FPS
3. **Accuracy Test**: Validate 95%+ accuracy on test swipes
4. **Stability Test**: Run for 10 minutes without degradation

## Security Considerations

1. **Camera Permissions**: 
   - Request explicit user permission
   - Handle denial gracefully
   - No background camera access

2. **Data Privacy**:
   - No frame storage by default
   - Optional logging excludes image data
   - Clear data retention policies

3. **Input Validation**:
   - Sanitize configuration inputs
   - Validate file paths
   - Prevent command injection

## Deployment Architecture

### Application Structure

```
Glide/
├── glide/
│   ├── app/
│   │   └── main.py          # Entry point
│   ├── core/
│   │   ├── types.py         # Data structures
│   │   └── config_models.py # Pydantic config models
│   ├── perception/
│   │   └── hands.py         # MediaPipe wrapper
│   ├── features/
│   │   ├── alignment.py     # Hand coordinate transform
│   │   └── fingerpose.py    # Pose detection
│   ├── gestures/
│   │   ├── touchproof.py    # Touch detection
│   │   ├── circular.py      # Circular gestures
│   │   └── kinematics.py    # Motion tracking
│   ├── ui/
│   │   ├── overlay.py       # HUD rendering
│   │   └── utils.py         # Display utilities
│   └── io/
│       ├── event_output.py  # JSON streaming
│       └── defaults.yaml    # Default config
├── models/
│   └── hand_landmarker.task # MediaPipe model
├── docs/
│   ├── TOUCHPROOF.md        # Touch detection details
│   └── ARCHITECTURE.md      # System architecture
├── requirements.txt
└── README.md
```

### Dependencies

```
opencv-python>=4.8.0
mediapipe>=0.10.14
numpy>=1.24.0
pyyaml>=6.0
pydantic>=2.0.0
```

## Future Extensibility

### Plugin Architecture

```python
class GesturePlugin(ABC):
    """Base class for gesture recognition plugins."""
    
    @abstractmethod
    def process(self, features: HandFeatures) -> Optional[GestureEvent]:
        """Process features and optionally emit gesture."""
```

### OS Integration Hooks

```python
class OSController(ABC):
    """Abstract base for OS-specific control."""
    
    @abstractmethod
    def execute_action(self, direction: str) -> None:
        """Execute OS-specific action for gesture."""
```

## Conclusion

This design provides the architecture for Glide's touchless gesture control system. The focus on multi-signal touch detection and circular gestures creates a practical solution for hands-free computer interaction - perfect for when you're eating and computing.