# Proposal: macOS Scrolling Integration

## Problem

Glide currently detects circular gestures and outputs JSON events, but cannot control macOS applications. Users need hands-free scrolling for reading PDFs, browsing web pages, and reviewing documents - especially when their hands are occupied (e.g., while eating).

The gap: Gesture detection works, but there's no bridge to actual system control.

## Success Metrics

1. **Latency**: < 150ms from gesture start to first scroll event
2. **Smoothness**: Scroll motion feels natural, matching finger rotation speed
3. **Accuracy**: 95%+ of intentional gestures produce expected scrolling
4. **False positives**: < 1 per 5-minute session
5. **CPU usage**: < 5% additional overhead for scroll generation

## Constraints / Non-Goals

### In Scope
- Vertical scrolling only (horizontal scroll is a non-goal for v1)
- Single-hand gestures only
- Local processing only (no cloud services)
- Preview, Safari, Chrome as primary targets

### Out of Scope
- Page navigation (PageUp/PageDown)
- Zoom gestures
- Multi-application awareness
- Custom per-app scroll speeds
- Windows/Linux support

## Alternatives Considered

1. **Virtual HID Device**
   - Pros: Works everywhere, no Accessibility permission
   - Cons: Complex driver signing, kernel extension requirements
   - Decision: Too complex for v1

2. **Keyboard Event Simulation (Arrow Keys)**
   - Pros: Simple, works in most apps
   - Cons: Jerky motion, no smooth scrolling
   - Decision: Poor user experience

3. **Native Helper App (Swift)**
   - Pros: Better security model, easier App Store distribution
   - Cons: More complex development, IPC overhead
   - Decision: Consider for v2, start with PyObjC monolith

4. **Browser Extension**
   - Pros: No system permissions needed for web
   - Cons: Limited to browsers only
   - Decision: Too limiting for general document reading

## Recommendation

Use PyObjC with Quartz Event Services (CGEventCreateScrollWheelEvent) for v1. This provides:
- Native smooth scrolling
- Works across all macOS apps
- Single Python process
- Straightforward implementation

Move to split Swift helper in v2 for better security and distribution.