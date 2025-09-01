# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - Unreleased (TODO, docs done)

### Added
- macOS native scrolling support using circular gestures
  - Clockwise gestures scroll down, counter-clockwise scrolls up
  - Configurable scroll speed (180° rotation ≈ 400 pixels)
  - Respects system natural scrolling preference
  - Visual HUD overlay showing scroll direction and velocity
- PyObjC dependency for macOS Quartz Event Services integration
- New `glide.runtime.actions` module for platform-specific scroll actions
- ScrollDispatcher for mapping circular gestures to scroll events
- QuartzScrollAction for generating native macOS scroll events
- ScrollHUD for visual feedback during scrolling

### Changed
- Extended configuration schema to include scroll settings
- Updated gesture pipeline to support scroll action dispatching

### Requirements
- macOS users now require Accessibility permissions for scroll functionality
- Added PyObjC framework dependencies for macOS integration

## [0.1.0] - 2024-12-31

### Added
- Initial release with core touchless gesture control
- TouchProof multi-signal fingertip detection system
- MediaPipe hand tracking with 21-point landmark detection
- Circular gesture recognition (clockwise/counter-clockwise)
- Real-time visual feedback with touch status and signal visualization
- Modular architecture with clean separation of concerns
- Configuration system with YAML support
- JSON event output for gesture detection
- Debug mode with detailed signal analysis
- FPS counter and performance monitoring

### Features
- Proximity-based finger touch detection
- Angle convergence analysis
- Micro-Flow Cohesion (MFC) optical flow tracking
- Configurable detection thresholds
- Headless mode for server deployment
- Event recording to JSONL format

### Technical
- Python 3.10+ support
- OpenCV integration for video capture
- NumPy for efficient computation
- Pydantic for configuration validation
- Comprehensive test suite
- Clean package structure with separation of concerns