# Dependencies

This document tracks all external dependencies for the Glide project, including rationale for selection and removal plans.

## Runtime Dependencies

### pyobjc-framework-Quartz
- **Version**: >= 8.0
- **Purpose**: Access to macOS Quartz Event Services for generating native scroll events
- **Used by**: `glide.runtime.actions.quartz_scroll`
- **Alternatives Considered**:
  - **pynput**: Cross-platform but less native integration, higher latency
  - **pyautogui**: No smooth scrolling support, keyboard simulation only
  - **cython + native**: Too complex for initial implementation
- **Removal Plan**: Will be removed if/when we implement native Swift helper app (v2)

### opencv-python (cv2)
- **Version**: >= 4.5.0
- **Purpose**: Camera capture and image processing
- **Used by**: `glide.perception.camera`
- **Alternatives Considered**:
  - **picamera**: Raspberry Pi only
  - **pygame.camera**: Limited platform support
  - **native capture**: Platform-specific complexity
- **Removal Plan**: Core dependency, no removal planned

### mediapipe
- **Version**: >= 0.10.0
- **Purpose**: Hand landmark detection and tracking
- **Used by**: `glide.perception.hands`
- **Alternatives Considered**:
  - **OpenPose**: Heavier, requires GPU
  - **Custom CNN**: Development complexity
  - **Apple Vision**: Platform-specific
- **Removal Plan**: Core dependency, no removal planned

### numpy
- **Version**: >= 1.20.0
- **Purpose**: Numerical computations for gesture detection
- **Used by**: Multiple modules for array operations
- **Alternatives Considered**:
  - **Pure Python**: Too slow for real-time
  - **numba**: Additional complexity
- **Removal Plan**: Core dependency, no removal planned

### pydantic
- **Version**: >= 2.0
- **Purpose**: Configuration validation and type safety
- **Used by**: `glide.core.config_models`
- **Alternatives Considered**:
  - **dataclasses**: No validation
  - **marshmallow**: More verbose
  - **cerberus**: Less type integration
- **Removal Plan**: Core dependency, no removal planned

### pyyaml
- **Version**: >= 6.0
- **Purpose**: Configuration file parsing
- **Used by**: `glide.io.config`
- **Alternatives Considered**:
  - **toml**: Less human-readable for nested config
  - **json**: No comments support
- **Removal Plan**: Core dependency, no removal planned

### tkinter
- **Version**: Built-in
- **Purpose**: Minimal UI overlays and HUD display
- **Used by**: `glide.ui.overlay`, `glide.runtime.ui.scroll_hud`
- **Alternatives Considered**:
  - **PyQt**: Heavier dependency
  - **Kivy**: Overkill for simple overlays
  - **PyObjC NSWindow**: More complex implementation
- **Removal Plan**: May migrate to native implementation in v2

## Development Dependencies

### pytest
- **Version**: >= 7.0
- **Purpose**: Test framework
- **Alternatives Considered**: unittest (less features), nose2 (less maintained)
- **Removal Plan**: None

### mypy
- **Version**: >= 1.0
- **Purpose**: Static type checking
- **Alternatives Considered**: pytype (slower), pyre (Facebook-specific)
- **Removal Plan**: None

## Model Files (Not Python Dependencies)

### hand_landmarker.task
- **Source**: MediaPipe pre-trained model
- **Purpose**: Hand detection and landmark extraction
- **Size**: ~25MB
- **Location**: `models/hand_landmarker.task`

### gesture_recognizer.task
- **Source**: MediaPipe pre-trained model
- **Purpose**: Basic gesture classification (unused in v1)
- **Size**: ~8MB
- **Location**: `models/gesture_recognizer.task`

## Platform Requirements

### macOS
- **Version**: 10.12+ (Sierra or later)
- **Reason**: Quartz Event Services API availability
- **Python**: 3.8+ (for typing features)

### Accessibility Permission
- **Required for**: Scroll event injection
- **API**: `AXIsProcessTrusted()`
- **User Flow**: System Preferences → Security & Privacy → Accessibility

## Installation Notes

```bash
# Core dependencies
pip install -r requirements.txt

# macOS-specific (for scrolling feature)
pip install pyobjc-framework-Quartz pyobjc-framework-AppKit

# Development dependencies
pip install -r requirements-dev.txt
```