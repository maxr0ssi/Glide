# Changelog

All notable changes to Glide will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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