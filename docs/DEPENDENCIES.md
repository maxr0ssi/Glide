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

### websockets
- **Version**: >= 12.0
- **Purpose**: WebSocket server for HUD communication
- **Used by**: `glide.runtime.ipc.ws`
- **Alternatives Considered**:
  - **aiohttp**: Heavier, full web framework
  - **tornado**: More complex for simple WebSocket needs
  - **socket.io**: Unnecessary overhead for local communication
- **Removal Plan**: Core dependency for HUD communication, no removal planned

### tkinter (DEPRECATED)
- **Version**: Built-in
- **Purpose**: Legacy UI overlays (moved to dev/)
- **Used by**: `dev.preview.overlay` (debug only)
- **Status**: Replaced by native macOS HUD
- **Removal Plan**: Kept for development/debugging only

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

## Native HUD Dependencies (Swift)

### macOS SDK
- **Version**: 12.0+ (Monterey)
- **Purpose**: NSPanel, NSVisualEffectView, Core Animation
- **Used by**: `apps/hud-macos/`

### Swift Package Dependencies
- None - Pure AppKit/Core Animation implementation

## Platform Requirements

### macOS
- **Version**: 12.0+ (Monterey or later)
- **Reason**: 
  - Quartz Event Services API for scrolling
  - NSVisualEffectView materials for HUD
  - Swift 5.5+ features
- **Python**: 3.10+ (for typing features)

### Accessibility Permission
- **Required for**: 
  - Scroll event injection
  - Global hotkey (CMD+CTRL+G) for HUD
- **API**: `AXIsProcessTrusted()`
- **User Flow**: System Preferences → Security & Privacy → Accessibility

### Camera Permission
- **Required for**: Camera access
- **User Flow**: System Preferences → Security & Privacy → Camera

## Installation Notes

### Python Backend
```bash
# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate

# Install all dependencies (includes macOS-specific)
pip install -r requirements.txt

# Download MediaPipe models
python setup_models.py

# Development dependencies (optional)
pip install -r requirements-dev.txt
```

### Native HUD (macOS)
```bash
# Build the HUD
cd apps/hud-macos
swift build --configuration release

# Or use the convenience script
./scripts/run_with_hud.sh
```

## WebSocket Protocol

The HUD communicates with the Python backend via WebSocket on `ws://127.0.0.1:8765/hud`:

### Messages from Backend → HUD
- `{"type": "scroll", "vy": float, "speed": float}` - Scroll events
- `{"type": "hide"}` - Hide HUD
- `{"type": "touchproof", "active": bool, "hands": int}` - TouchProof status
- `{"type": "camera", "frame": base64, "width": int, "height": int}` - Camera frames
- `{"type": "config", "position": str, "opacity": float}` - Initial config

### Messages from HUD → Backend
- `{"type": "mode", "expanded": bool}` - Mode change notification