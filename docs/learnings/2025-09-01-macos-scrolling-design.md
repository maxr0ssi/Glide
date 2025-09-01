# Learnings — macOS Scrolling Design

### PATCH SUMMARY
- Mode: Designing
- Changed files:
  - docs/designs/macos-scrolling/DESIGN.md
  - docs/designs/macos-scrolling/subsystems/scroll-dispatcher.md
  - docs/designs/macos-scrolling/subsystems/quartz-scroll-action.md
  - docs/designs/macos-scrolling/subsystems/scroll-hud.md
  - docs/DEPENDENCIES.md
  - docs/learnings/2025-09-01-macos-scrolling-design.md
- Why: Created technical design for macOS scrolling feature to bridge circular gestures to native scroll events
- How: Designed three-layer architecture with ScrollDispatcher coordinating platform-specific QuartzScrollAction and optional ScrollHUD
- Tests: Specified unit, integration, and architecture test strategies covering permissions, natural scrolling, and performance
- Risks & Mitigations: 
  - Accessibility permission required (guided setup flow)
  - Thread safety for Quartz APIs (main thread enforcement)
  - Natural scrolling detection (fallback defaults)

## What surprised us

1. **Quartz Event Thread Requirements**: All Quartz Event Services calls must happen on the main thread, requiring careful dispatch handling in the design.

2. **Natural Scrolling Complexity**: The system preference for natural scrolling isn't directly exposed via a clean API, requiring NSUserDefaults inspection.

3. **Permission State Monitoring**: Accessibility permissions can be revoked while the app is running, requiring dynamic permission checking rather than just startup validation.

## Decisions made (and why)

1. **PyObjC over Native Extension**: Chose PyObjC for v1 implementation to maintain single Python process and faster iteration, despite potential for a Swift helper app in v2.

2. **Fire-and-Forget Event Model**: Scroll events don't return success/failure from the OS level, so we adopted an optimistic dispatch pattern with permission pre-checking.

3. **Pixel-Based Mapping**: Used direct pixel units for scroll events rather than line-based scrolling for more consistent cross-application behavior.

4. **Minimal HUD with Tkinter**: Selected tkinter for HUD despite its limitations because it's bundled with Python and sufficient for simple overlay needs.

5. **180° = 400px Mapping**: This ratio provides intuitive scrolling where a half-circle rotation scrolls about one "page" of content.

## Follow-ups

1. **Momentum Scrolling Investigation**: Need to research CGEventSetIntegerValueField for momentum phase flags to get native-feeling deceleration.

2. **Multi-Display Testing**: Design assumes single display; need to verify behavior with multiple monitor setups.

3. **Performance Profiling**: The < 5% CPU overhead target needs validation with real implementation.

4. **Application Compatibility Matrix**: Should document which apps work well with synthetic scroll events (Preview, Safari, Chrome) vs those that might need special handling.