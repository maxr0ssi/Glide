# Changelog

All notable changes to Glide will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - Native macOS HUD Implementation (Phase 4)
- **Implemented native Swift macOS HUD application**:
  - Pure AppKit/Core Animation UI (no WebView)
  - NSPanel floating window with CMD+CTRL+G hotkey activation
  - Two display modes:
    - Minimized (300x150px): Direction arrows and speed bars
    - Expanded (500x400px): Adds live camera feed with hand tracking overlay
  - "Liquid nitrogen ice" aesthetic with translucent glass effects
  - Auto-hide in minimized mode (2s delay), always visible in expanded
  - TouchProof status indicator with cyan glow when active
  - Performance optimized camera streaming (throttled, JPEG compression)
  - Thread-safe WebSocket communication with Python backend
- **Extended WebSocket Protocol**:
  - Added camera frame streaming: `{"type": "camera", "frame": base64, "width": int, "height": int}`
  - Added TouchProof events: `{"type": "touchproof", "active": bool, "hands": int}`
  - Added mode notifications: `{"type": "mode", "expanded": bool}`
  - Camera frames only sent to clients in expanded mode
- **Created comprehensive documentation**:
  - `docs/HUD.md` - Complete HUD architecture and usage guide
  - Updated README.md with HUD setup instructions
  - Added run scripts for easy testing

### Changed - Code Quality Improvements
- **Improved Error Handling**:
  - Replaced generic `Exception` catches with specific exception types
  - Added proper error messages with context
  - Better error handling in WebSocket, MediaPipe, and file operations
- **Configuration Management**:
  - Added `camera_throttle_hz` and `camera_frame_skip` to ScrollConfig
  - Created `OpticalFlowConfig` for optical flow parameters
  - Moved hardcoded values to configuration files
  - Extended config models with proper validation
- **Logging Improvements**:
  - Replaced print statements with proper logging in `setup_models.py`
  - Consistent use of logger throughout codebase
  - Removed debug print statements from production code
- **Code Cleanup**:
  - Fixed PEP 8 compliance issues
  - Added missing type hints
  - Improved docstring coverage
  - Removed redundant imports and dead code

### Fixed
- Fixed thread safety issues in HUD by wrapping UI updates in DispatchQueue.main.async
- Fixed window sizing issues (3-5px bug) with proper frame initialization
- Fixed expand button not working due to alpha value and hitTest issues
- Fixed auto-hide behavior to never hide in expanded mode
- Fixed FPS drops by optimizing camera frame throttling
- Fixed undefined `target_clients` error in WebSocket broadcaster
- Fixed keyboard interrupt cleanup with proper signal handlers

### Removed
- Removed legacy web-based HUD approach in favor of native implementation
- Removed debug logging statements throughout codebase
- Removed test scripts and temporary files

### Added - WebSocket HUD Broadcasting (Phase 2)
- **Implemented WebSocket server for HUD events**:
  - Created `glide/runtime/ipc/ws.py` with localhost-only WebSocket broadcaster
  - Broadcasts scroll events: `{"type": "scroll", "vy": float, "speed": 0-1}`
  - Sends hide events when scrolling stops: `{"type": "hide"}`
  - Throttled to 60 Hz by default (configurable 30-120 Hz)
  - Optional session token authentication for security
- **Integrated WebSocket with scroll system**:
  - VelocityScrollDispatcher now publishes events to WebSocket clients
  - Added WebSocket configuration to ScrollConfig and config models
  - New CLI flags: `--hud-port` and `--hud-token`
- **Added test client**:
  - `tools/test_ws_client.py` for testing WebSocket connectivity
- **Dependencies**:
  - Added `websockets>=12.0` to requirements.txt

### Changed - Repository Restructuring (Phase 1)
- **Restructured repository for backend/frontend separation**:
  - Moved `glide/ui/overlay.py` to `dev/preview/overlay.py` (debug-only tool)
  - Moved `glide/ui/utils.py` to `dev/preview/utils.py`
  - Moved `glide/runtime/ui/scroll_hud.py` to `glide/runtime/hud/legacy_tk_hud.py`
  - Created `configs/defaults.yaml` (copied from `glide/io/defaults.yaml`, kept for compatibility)
- **Added new directory structure for future phases**:
  - `glide/runtime/ipc/` for WebSocket IPC (Phase 2)
  - `web/hud/` for web-based HUD (Phase 3)
  - `apps/hud-macos/` for Swift macOS app (Phase 4)
  - `dev/` for development-only tools
- **Created placeholder files for future implementation**:
  - WebSocket broadcaster stub in `glide/runtime/ipc/ws.py`
  - Web HUD scaffolding (package.json, index.html, TypeScript files)
  - macOS app README and directory structure

### Removed - Complete CircularEvent and Legacy Code Overhaul
- **Removed All CircularEvent Dependencies**:
  - Deleted `scroll.py` and `quartz_scroll.py` (legacy ScrollDispatcher and macOS implementation)
  - Deleted `circular.py`, `angle_stream.py`, `wheel_controller.py` (circular gesture detection)
  - Deleted `event_output.py` and `replay.py` (event emission system)
  - Removed all test files for circular events
  - Removed `docs/archive/` folder with old documentation
- **Updated Scroll HUD**:
  - Changed from circular arrows to vertical arrows
  - Now uses velocity directly: `show_scroll(velocity_y, normalized_speed)`
  - Progressive speed bars for visual feedback
- **Removed Configuration Legacy**:
  - Deleted `circular` section from `defaults.yaml`
  - Deleted `two_finger` legacy correlation settings
  - Removed `CircularConfig` and `TwoFingerConfig` classes
- **Architecture Simplification**:
  - No more synthetic CircularEvent creation
  - Direct velocity → scroll action pipeline
  - Created new `config.py` for clean ScrollConfig separation
  - ~1,500+ lines of legacy code removed

### Removed - Redundancy Cleanup
- **Deleted Unused Modules**:
  - `gestures/registry.py` - Entire unused gesture registry system
- **Removed Unused Types**:
  - `Mode` enum (ONE_FINGER, TWO_FINGER) from `types.py`
  - `EventSink` abstract class from `contracts.py`
- **Cleaned Up Dead Code**:
  - Pipeline.py: Removed unused imports, variables, and dead calculations
  - Removed unused configuration options: `log_level`, `log_file`, `show_fps`, `show_landmarks`, `show_confidence`
- **Import Cleanup**:
  - Removed all `# noqa: F401` comments
  - Cleaned up unused imports across all files
  - ~200+ lines of redundant code removed

### Added - Velocity-Based Scrolling (Latest)
- **Velocity-Based Continuous Scrolling** - Revolutionary new approach:
  - Direct velocity tracking of fingertip movement (pixels/second)
  - Native macOS scroll phases (began → changed → ended)
  - Automatic momentum handoff to macOS for buttery-smooth scrolling
  - Frame-rate independent operation
  - VelocityTracker component for real-time velocity calculation
  - VelocityController for simplified state management
  - ContinuousScrollAction using proper CGEvent phases
  - VelocityScrollDispatcher for clean event lifecycle
- Removed angle accumulation complexity in favor of direct velocity
- Much simpler and more intuitive scrolling experience

### Added - Initial Smooth Scrolling
- **Smooth Scrolling System** - Complete overhaul of scrolling behavior:
  - Virtual scroll wheel with continuous velocity control
  - Momentum physics - scrolling continues with natural deceleration after release
  - High-five gesture for instant stop
  - Single finger continuation after 1.5s delay
  - AngleStream component for per-frame angle tracking
  - WheelController state machine (IDLE → CLUTCH → SCROLL → MOMENTUM)
- macOS scrolling integration using PyObjC and Quartz Event Services
- ScrollDispatcher component for routing circular gestures to platform actions
- QuartzScrollAction for generating native macOS scroll events
- ScrollHUD overlay showing scroll direction with fade animations
- Configurable scroll parameters (pixels per degree, max velocity, natural scrolling)
- Accessibility permission detection and guidance
- Test scripts for PyObjC integration and scroll functionality

### Changed
- **Complete Scrolling Rewrite** - From angle-based to velocity-based approach
- Replaced AngleStream with VelocityTracker for direct velocity measurement
- Replaced WheelController with simplified VelocityController
- Updated ScrollDispatcher to use native scroll phases
- Improved pixels_per_degree default from 2.22 to 5.0 for better responsiveness

### Removed
- Angle accumulation system (AngleStream)
- Complex state machine (IDLE → CLUTCH → SCROLL → MOMENTUM)
- Manual momentum calculation (now handled by macOS)
- Discrete circular event fallback

### Technical Details - Velocity-Based System
- Direct velocity tracking in normalized coordinates (0-1)
- Simple 2-state machine: IDLE → SCROLLING (macOS handles momentum)
- Uses CGEventCreateScrollWheelEvent with proper scroll phases
- CGEventSetIntegerValueField for phase management
- CGEventSetDoubleValueField for sub-pixel precision
- EMA smoothing (α=0.3) for velocity stability
- 100ms sliding window for velocity calculation
- Native integration with macOS scroll acceleration
- Frame-rate independent (velocity in pixels/second)
