# Glide: Touch-Free Gesture Control

## The Problem

I was eating a burrito and trying to scroll through an article on my MacBook. Greasy fingers, expensive keyboard. You see the conflict. I thought: my laptop has a webcam right there, staring at me. What if it could just *watch* my hand and scroll for me?

What started as a weekend hack turned into a proper gesture recognition system with multi-signal sensor fusion, a native macOS HUD, and eventually a browser port you can try right now.

## The Idea

The concept is simple: pinch your index and middle fingers together, move them up or down, and the page scrolls. Release them to stop. No gloves, no special hardware. Just your webcam and a hand.

Under the hood, that means: detect a hand in video, figure out if two fingertips are actually touching, measure how fast they're moving, and translate that into native scroll events. Each of those steps has its own set of problems.

## How It Works: The Python Core

The detection pipeline looks like this:

```
Camera > MediaPipe > 21 Landmarks > TouchProof > Velocity > Scroll
```

MediaPipe gives me 21 3D hand landmarks per frame at ~15ms on an M1. That's the easy part. The hard part is figuring out if two fingertips are actually *touching* when all you have is a 2D image of a 3D scene.

### TouchProof: Detecting Contact from a Flat Image

This is the core algorithm. A camera can't measure depth, so a simple distance check between fingertip pixels fails constantly. Fingers can *look* close together from certain angles without touching, or actually touch while appearing far apart.

TouchProof solves this by combining multiple independent signals that fail in different ways:

- **Proximity**: normalized distance between fingertips (scaled by hand size so it works at any distance from the camera)
- **Angle**: convergence angle between the two finger directions. Parallel fingers that point toward each other are likely touching.
- **Optical flow cohesion (MFC)**: if two fingertips are moving as a single unit, they're probably stuck together. Computed by correlating their motion over a sliding window.

Each signal is good at detecting touch in some conditions and terrible in others. Proximity fails at extreme angles. Optical flow fails when the hand is stationary. Angle fails when fingers are close but not converging. That's the whole point: their failure modes don't overlap.

The signals get fused with weights that adapt based on hand distance:

```python
# Distance-aware fusion (simplified)
weights = get_adaptive_weights(distance_factor)

fused_score = (
    weights["proximity"] * proximity_score
    + weights["angle"]    * angle_score
    + weights["mfc"]      * mfc_score
)

is_touching = state_machine(fused_score)  # hysteresis prevents flickering
```

When the hand is far from the camera, proximity and optical flow dominate (pixel-level analysis is unreliable at distance). When it's close, geometric signals like angle carry more weight. In between, the weights interpolate linearly.

A few other things make it robust: everything is normalized by hand size (finger length in pixels) for scale invariance. Volatile signals get EMA smoothing to reduce jitter. And the final decision runs through a state machine with separate enter/exit thresholds (hysteresis) so you don't get rapid on-off flickering at the boundary.

The result: >95% detection accuracy across varying distances, lighting, and hand sizes, at under 5ms per frame.

## The HUD: A Tiny Bit of Swift

I wanted visual feedback that you'd barely notice. The answer: a 32x32 pixel pulse ring. That's it. ~400 lines of Swift.

```
◯  Idle (dim white, 20% opacity)
◉  Active (cyan pulse, breathing animation)
◉↑ Scrolling up
◉↓ Scrolling down
```

The ring communicates everything through color and animation. Idle is a faint white circle. When your fingers touch, it shifts to cyan with a breathing pulse. Start scrolling, and a tiny arrow appears inside. The opacity maps to scroll speed, where faster movement = brighter ring.

Implementation-wise, it's an `NSPanel` (not `NSWindow`, since panels can float above everything without stealing focus) with a `CAShapeLayer` for GPU-accelerated animation. The whole thing redraws a 32x32 pixel area, so the GPU cost is essentially zero.

The HUD connects to the Python backend over WebSocket. Why WebSocket for IPC between two local processes? Clean separation. The Python side doesn't know or care what's displaying its data; it just broadcasts events. This decoupling is what made the web port possible later. When I wanted to run the same pipeline in a browser, the architecture was already designed for it.

## Architecture

Here's how the pieces connect:

```
┌─────────────┐     ┌───────────────┐     ┌──────────────┐
│   Webcam    │────>│ Python Backend│────>│ macOS Scroll  │
│  (720p/60)  │     │  (Detection)  │     │  (CGEvent)    │
└─────────────┘     └───────┬───────┘     └──────────────┘
                            │ WebSocket
                    ┌───────▼───────┐
                    │   Swift HUD   │
                    │  (Pulse Ring) │
                    └───────────────┘
```

The Python backend is organized as a clean pipeline:

```
perception/    > Hand detection (MediaPipe wrapper)
features/      > Coordinate alignment, kinematics tracking
gestures/      > TouchProof fusion, velocity calculation
runtime/       > Scroll dispatch, WebSocket broadcast
```

Each layer only talks to the one below it. Perception doesn't know about gestures. Gestures don't know about scrolling. This made the codebase easy to reason about and, critically, easy to port.

**Key engineering decisions:**

- **MediaPipe**: 15ms per frame on M1. Fast enough for real-time, accurate enough for reliable landmark detection.
- **Velocity-based scrolling**: instead of mapping finger *position* to scroll position, I map finger *velocity*. This integrates naturally with macOS momentum scrolling, so releasing your fingers feels like lifting off a trackpad.
- **WebSocket IPC**: decoupled, extensible, and exactly what made the web port straightforward.

## Building with AI

I wanted for this to be useable in my website, but it was written in python. So I had two options:
    1. Create a server and API
    2. Convert to typescript

I did not want to add to ever going server fees...

So, I thougt two birds one stone. Get better at using AI tools and convert it to TS. I used Claude Code to port the entire detection pipeline from Python to TypeScript, roughly 3,000 lines of algorithm code.

The workflow: I'd specify what I wanted ("port `touchproof_detector.py` to TypeScript, preserving the scoring logic"), review the output, catch the places where Python idioms don't translate directly, and iterate. The actual algorithm code ported almost 1:1. Only three NumPy calls needed replacing: `np.log` to `Math.log`, `np.clip` to `Math.max/min`, `np.exp` to `Math.exp`.

The parts that needed human judgment were different from what I expected. The algorithm translation was mechanical. Claude handled it well. What required real tuning was the *feel*: scroll direction (inverted by default vs. the Python version), velocity multiplier (too fast in the browser), and touch detection delay (the web port's `requestAnimationFrame` loop runs at a different cadence than Python's `while True`). Those are the kinds of decisions that come from actually using the thing, not from reading the code.

The result: 78 passing tests across 10 files, cross-validated against Python by generating JSON test fixtures from the original code and verifying the TypeScript produces identical outputs.

The meta-lesson: using AI tools effectively on a real project is a skill worth practicing. Knowing *what* to delegate, *what* to review carefully, and *what* to tune by hand is the difference between a useful workflow and a frustrating one.

## Try It Yourself: The Web Port

That's what's running on the left side of this page right now.

The TypeScript port runs the same detection pipeline entirely in your browser. MediaPipe ships as a WASM module, so your camera feed never leaves your machine. No server, no uploads, everything client-side.

The integration point is a single React hook:

```typescript
const { videoRef, signals, gestureState, landmarks, fps } = useGlide();
```

Camera access, MediaPipe initialization, landmark detection, coordinate alignment, TouchProof scoring, velocity tracking, all wired up in one call. You get back the raw signals and the final gesture state on every frame.

A few things changed in the port. Optical flow (MFC) is excluded because OpenCV's `calcOpticalFlowPyrLK` has no browser equivalent, so the MFC score is hardcoded to a neutral 0.5. Python's `deque(maxlen=N)` became a custom `BoundedDeque<T>` ring buffer. And `requestAnimationFrame` replaced `setInterval`, which naturally throttles to the display refresh rate and pauses when the tab is hidden.

If you have a webcam, try it: pinch your index and middle fingers together and move them up or down. The signal dashboard shows you what the algorithm sees in real-time.

## What's Next

I have ideas for where this could go: multi-hand support for zooming and video playback control, a way to record and replay custom gestures, and cross-platform support beyond macOS. But honestly, the original goal is complete: I can eat lunch and scroll without getting crumbs on my keyboard.
