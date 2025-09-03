# Velocity-Based Scrolling Implementation

## Overview

Glide now uses a revolutionary velocity-based scrolling system that tracks fingertip movement directly, providing a more natural and intuitive scrolling experience on macOS.

## Architecture

### Core Components

1. **VelocityTracker** (`glide/gestures/velocity_tracker.py`)
   - Tracks fingertip positions over a 100ms sliding window
   - Calculates instantaneous velocity in pixels/second
   - Applies exponential moving average (EMA) smoothing
   - Frame-rate independent operation

2. **VelocityController** (`glide/gestures/velocity_controller.py`)
   - Simplified state machine: IDLE → SCROLLING
   - Direct velocity passthrough
   - High-five gesture for instant stop
   - No manual momentum calculation (handled by macOS)

3. **ContinuousScrollAction** (`glide/runtime/actions/continuous_scroll.py`)
   - Uses native macOS scroll phases
   - Proper CGEvent creation with phase management
   - Sub-pixel precision using CGEventSetDoubleValueField
   - Automatic momentum handoff to macOS

4. **VelocityScrollDispatcher** (`glide/runtime/actions/velocity_dispatcher.py`)
   - Manages scroll gesture lifecycle
   - Handles state transitions
   - Clean phase-based event dispatch

## Key Improvements

### From Angle-Based to Velocity-Based

**Old System (Angle-Based)**:
- Tracked rotation angles between fingertips
- Complex 4-state machine (IDLE → CLUTCH → SCROLL → MOMENTUM)
- Manual momentum calculation
- Frame-dependent behavior
- Accumulation artifacts

**New System (Velocity-Based)**:
- Direct velocity measurement in pixels/second
- Simple 2-state machine (IDLE → SCROLLING)
- macOS handles all momentum
- Frame-rate independent
- Smooth, natural feel

### Technical Implementation

```python
# Velocity calculation (simplified)
velocity_x = (current_x - previous_x) / time_delta
velocity_y = (current_y - previous_y) / time_delta

# Scroll phase management
CGEventSetIntegerValueField(event, kCGScrollWheelEventScrollPhase, phase)
CGEventSetDoubleValueField(event, kCGScrollWheelEventPointDeltaAxis1, delta_y)
```

### Benefits

1. **Natural Feel**: Movement directly maps to scroll speed
2. **Native Integration**: Uses macOS scroll phases properly
3. **Simplicity**: Much less code, easier to maintain
4. **Performance**: Frame-rate independent, no accumulation
5. **Precision**: Sub-pixel scroll deltas for smooth motion

## Configuration

The system respects existing configuration but interprets it differently:

```yaml
scroll:
  enabled: true
  pixels_per_degree: 5.0  # Legacy, used for velocity scaling
  max_velocity: 100.0     # Maximum pixels per event
  respect_system_preference: true
```

## Usage

1. Touch index and middle fingertips together
2. Move fingers up/down to scroll
3. Release for momentum (handled by macOS)
4. High-five to stop instantly

The velocity directly controls scroll speed - move faster to scroll faster!