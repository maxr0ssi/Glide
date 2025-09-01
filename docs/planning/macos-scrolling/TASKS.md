# macOS Scrolling Implementation Tasks

## Overview
Break down the macOS scrolling feature into ≤2-day tasks with clear acceptance criteria.

## Task 1: PyObjC Integration & Basic Scroll Events
**Duration**: 1 day  
**Dependencies**: None

### Acceptance Criteria
- [ ] PyObjC added to requirements.txt
- [ ] Test script demonstrates CGEventCreateScrollWheelEvent
- [ ] Natural scrolling preference detected correctly
- [ ] Unit tests for scroll event generation

### Test Plan
- Unit: Mock Quartz APIs, verify event parameters
- Integration: Actual scroll events in test window
- Manual: Verify scrolling in Preview.app

---

## Task 2: ScrollDispatcher Implementation
**Duration**: 1 day  
**Dependencies**: Task 1

### Acceptance Criteria
- [ ] CircularEvent → ScrollIntent conversion working
- [ ] Angle-to-pixels mapping (180° = 400px)
- [ ] Direction mapping (CW = down, CCW = up)
- [ ] Basic configuration loading from defaults.yaml
- [ ] Unit tests for core functionality

### Test Plan
- Unit: Test gesture mappings and basic cases
- Integration: End-to-end gesture → scroll pipeline
- Manual: Verify expected scroll behavior

### POC Simplifications
- No thread safety needed (single-threaded)
- Direct function calls (no event queue)
- Simple console logging for errors

---

## Task 3: QuartzScrollAction Implementation
**Duration**: 1 day  
**Dependencies**: Task 2

### Acceptance Criteria
- [ ] Basic scroll events using CGEventCreateScrollWheelEvent
- [ ] Natural scrolling preference detected
- [ ] Console logging for permission errors
- [ ] Integration tests with real Quartz APIs

### Test Plan
- Integration: Verify scroll events in Preview/Safari
- Performance: Check basic latency
- Manual: Test with/without Accessibility permission

### POC Simplifications
- Simple event creation (no momentum)
- One-time preference detection
- Basic error logging only

---

## Task 4: Minimal HUD Overlay
**Duration**: 0.5 day  
**Dependencies**: Task 3

### Acceptance Criteria
- [ ] Circular arrow indicator on gesture
- [ ] Fade in/out animations
- [ ] Non-blocking overlay window
- [ ] Dark mode support

### Test Plan
- Visual: Screenshot tests
- Integration: HUD appears/disappears correctly
- Performance: No impact on scroll latency

---

## Task 5: Integration & Polish
**Duration**: 0.5 day  
**Dependencies**: Tasks 1-4

### Acceptance Criteria
- [ ] Full pipeline working end-to-end
- [ ] Configuration via defaults.yaml
- [ ] README updated with setup instructions
- [ ] CHANGELOG entry added
- [ ] All tests passing

### Test Plan
- System: 5-minute usage session without issues
- Cross-app: Preview, Safari, Chrome all scroll correctly
- User acceptance: Natural feel, < 1 false positive

---

## Risk Mitigation
1. **Accessibility permission**: Detect early, log clear instructions
2. **Main thread**: Ensure Quartz calls from main thread
3. **Performance**: Basic latency check, optimize later if needed
4. **Compatibility**: Test on macOS 12+ (Monterey minimum)

---

## Deferred Features (Post-POC)
The following features are documented in the design but deferred:
- Thread safety and event queuing
- Complex error recovery and retry logic
- Event validation and parameter bounds checking
- Architecture tests
- Permission state monitoring
- Momentum scrolling
- Per-app configuration