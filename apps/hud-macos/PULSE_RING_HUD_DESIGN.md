# Pulse Ring HUD - Design Document

## Overview
A minimalist heads-up display for Glide that uses a single animated ring to communicate gesture tracking status and scroll direction. The HUD prioritizes being unobtrusive while providing clear visual feedback.

## Design Philosophy
- **Minimal**: Single visual element that communicates all states
- **Unobtrusive**: Small, translucent, positioned out of the way
- **Elegant**: Smooth animations and subtle visual feedback
- **Intuitive**: Clear visual language that requires no explanation

## Visual Specifications

### Dimensions
- **Window Size**: 32x32 pixels
- **Ring Diameter**: 24 pixels
- **Ring Stroke Width**: 3 pixels
- **Arrow Size**: 8x8 pixels (when shown)

### Position
- **Default**: Top-right corner
- **Offset**: 20px from top edge, 20px from right edge
- **Alternative positions**: Top-left, bottom-right, bottom-left

### Colors & Opacity
```
Idle State:
- Ring: rgba(255, 255, 255, 0.2) - 20% white
- Background: Transparent

Active State:
- Ring: rgba(100, 200, 255, 0.8) - 80% soft cyan
- Pulse range: 0.4 to 1.0 opacity
- Background: Transparent

Scroll Indicators:
- Arrow: rgba(100, 200, 255, 0.9) - 90% soft cyan
- Fast scroll: Ring brightens to 100% opacity
```

## States & Behaviors

### 1. Idle (No Tracking)
- **Visual**: Dim white ring, static
- **Opacity**: 20%
- **Animation**: None
- **Duration**: Persistent

### 2. Active (Tracking, No Movement)
- **Visual**: Cyan ring with breathing effect
- **Animation**:
  - Opacity pulse: 0.4 → 0.8 → 0.4 (2s cycle, ease-in-out)
  - Scale pulse: 1.0 → 1.05 → 1.0 (2s cycle, synchronized)
- **Transition**: Fade from idle over 0.3s

### 3. Scrolling Up
- **Visual**: Cyan ring + upward arrow (↑) inside
- **Animation**:
  - Ring opacity maps to scroll speed (0.6 min, 1.0 max)
  - Arrow fades in over 0.15s
  - Arrow has subtle upward float animation
- **Transition**: Arrow fades out 0.3s after scroll stops

### 4. Scrolling Down
- **Visual**: Cyan ring + downward arrow (↓) inside
- **Animation**: Same as scrolling up but arrow points down
- **Arrow position**: Centered in ring

### 5. Hidden
- **Visual**: Completely hidden
- **Reappear**: Via hotkey (CMD+CTRL+G) or app restart

## Interaction Design

### Mouse Interactions
1. **Hover**:
   - Shows small × in top-right corner of ring
   - × appears with 0.2s fade-in
   - Ring slightly brightens (+10% opacity)

2. **Click on ×**:
   - Hides HUD permanently
   - Saves preference to UserDefaults

3. **Right-click on ring**:
   - Shows context menu (see below)

### Context Menu Structure
```
┌─────────────────────────┐
│ Visibility              │
│ ├─ Always Show      ✓   │
│ ├─ Auto-hide (2s)       │
│ └─ Hidden               │
├─────────────────────────┤
│ Position                │
│ ├─ Top Right        ✓   │
│ ├─ Top Left             │
│ ├─ Bottom Right         │
│ └─ Bottom Left          │
├─────────────────────────┤
│ Quit Glide HUD          │
└─────────────────────────┘
```

## Auto-hide Behavior
When "Auto-hide" is selected:
1. HUD appears when scroll activity detected
2. Remains visible during scrolling
3. Fades out 2 seconds after last scroll event
4. Fade out duration: 0.5s

## Technical Implementation

### Window Configuration
```swift
- NSPanel (not NSWindow)
- Style: .nonactivatingPanel
- Level: .floating
- Collection behavior: .canJoinAllSpaces
- Opaque: false
- Background: clear
- Has shadow: false
```

### Layer Structure
```
HUDWindow
└── ContentView (32x32)
    ├── RingLayer (CAShapeLayer)
    │   └── Ring path (24px diameter)
    ├── ArrowLayer (CAShapeLayer)
    │   └── Arrow path (8x8, centered)
    └── CloseButton (NSButton, hidden by default)
        └── × symbol
```

### Animation Specifications
1. **Breathing Pulse**:
   - Duration: 2.0s
   - Timing: ease-in-out
   - Repeat: infinite
   - Autoreverses: true

2. **Scroll Speed Mapping**:
   - Input: 0.0 to 1.0 (normalized scroll speed)
   - Output: 0.6 to 1.0 (ring opacity)
   - Function: linear mapping

3. **Transitions**:
   - State changes: 0.3s ease-out
   - Arrow fade: 0.15s ease-in (appear), 0.3s ease-out (disappear)

### Performance Considerations
- Use CAShapeLayer for GPU acceleration
- Reuse layers instead of creating/destroying
- Batch animations when possible
- Minimal redraw area (32x32 pixels)

## Preferences Storage
Store in UserDefaults:
- `glide.hud.visibility`: "always" | "autohide" | "hidden"
- `glide.hud.position`: "top-right" | "top-left" | "bottom-right" | "bottom-left"
- `glide.hud.lastHidden`: timestamp of last hide action

## Accessibility
- VoiceOver label: "Glide gesture tracking indicator"
- Keyboard navigation: CMD+CTRL+G to toggle visibility
- High contrast mode: Increase ring stroke width to 4px

## Future Enhancements (Not in MVP)
- Color customization
- Size options (small/medium/large)
- Custom positioning (drag to reposition)
- Multiple display support

## Implementation Phases

### Phase 1: Core Ring (MVP)
1. Basic window setup (32x32, positioned top-right)
2. Ring drawing with CAShapeLayer
3. State management (idle/active/scrolling)
4. Basic animations (breathing pulse)
5. WebSocket integration

### Phase 2: Interactions
1. Hover state and × button
2. Context menu
3. Position preferences
4. Visibility modes

### Phase 3: Polish
1. Smooth transitions
2. Arrow animations
3. Auto-hide functionality
4. Preferences persistence
