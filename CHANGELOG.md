# Changelog

All notable changes to Glide will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2025-11-04

### Added
- **Velocity-Based Scrolling**: Natural continuous scrolling that follows your finger movement speed
  - Move fingers faster to scroll faster, slower to scroll slower
  - Native macOS momentum - system handles smooth deceleration when you release
  - High-five gesture for instant stop
- **TouchProof Detection**: Multi-signal fusion system for accurate fingertip touch detection
  - Adaptive proximity detection works at varying distances from camera
  - Optimized for MacBook Pro built-in cameras
- **Visual Feedback**: Real-time HUD showing touch status, scroll direction, and velocity

### Changed
- **Documentation Cleanup**: Removed marketing language, emojis, and unproven performance claims
  - Toned down language throughout (no more "revolutionary", "advanced", etc.)
  - Reorganized docs structure with `docs/algorithms/` for technical deep-dives
  - Updated README to use Makefile commands
  - Condensed CHANGELOG to user-facing changes only
- **Code Organization**: Refactored touchproof.py from 577-line monolith into clean modules
  - Split into 4 files: signals, scoring, detector, and public API
  - Removed ~10 lines of dead code (unused methods and variables)
  - Better separation of concerns (pure functions vs state management)
- Scrolling system completely rewritten for more responsive and natural feel
- Improved default scroll sensitivity for better control

### Removed
- Legacy circular gesture system
- Angle-based scrolling (replaced with direct velocity tracking)
- Dead code: unused scroll_hud.py, empty directories, duplicate docs
