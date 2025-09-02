# Changelog

All notable changes to Glide will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- macOS scrolling integration using PyObjC and Quartz Event Services
- ScrollDispatcher component for routing circular gestures to platform actions
- QuartzScrollAction for generating native macOS scroll events
- ScrollHUD overlay showing scroll direction with fade animations
- Configurable scroll parameters (pixels per degree, max velocity, natural scrolling)
- Accessibility permission detection and guidance
- Test scripts for PyObjC integration and scroll functionality

### Changed
- Updated requirements.txt to include pyobjc-framework-Quartz
- Extended AppConfig to include ScrollConfig section
- Updated defaults.yaml with scroll configuration parameters
- Enhanced README with macOS setup instructions and scrolling controls

### Technical Details
- Circular gestures now trigger native scroll events on macOS
- 180 degrees of rotation = 400 pixels of scroll distance
- Respects system natural scrolling preference
- Thread-safe HUD implementation using tkinter
- POC implementation focused on simplicity over features