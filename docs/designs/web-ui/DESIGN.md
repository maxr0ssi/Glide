*Version 0.1.0 · Updated 2026-02-12*

# Web UI — Technical Design

## Context & Goals (link proposal)

Port Glide's core gesture detection algorithms to TypeScript for a browser-based demo. Goals:

1. Standalone Vite app at `apps/web-ui/` (matches `apps/hud-macos/` pattern)
2. Exportable `<GlideDemo />` React component for embedding
3. Split-view UX: algorithm visualizer + scrollable demo content

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    useGlide Hook                         │
│                                                         │
│  getUserMedia → video                                   │
│        ↓                                                │
│  WebHandDetector (MediaPipe WASM)                       │
│        ↓                                                │
│  HandAligner → KinematicsTracker → checkHandPose        │
│        ↓                                                │
│  TouchProofDetector (scoring → state machine)           │
│        ↓                                                │
│  VelocityTracker → VelocityController                   │
│        ↓                                                │
│  { signals, velocity, gestureState, landmarks, fps }    │
└─────────────────────────────────────────────────────────┘
         ↓                          ↓
   ┌───────────┐          ┌──────────────┐
   │ Visualizer│          │  ScrollArea  │
   │  (canvas) │          │ (scrollBy)   │
   └───────────┘          └──────────────┘
```

## Public Interfaces

### Exported from `src/index.ts`

- `GlideDemo` — top-level React component
- `useGlide` — orchestration hook
- Type exports: `GateState`, `Landmark`, `HandDet`, `PoseFlags`, `AppConfig`, `TouchProofConfig`, `TouchProofSignals`, `GestureState`, `VelocityUpdate`, `Vec2D`

### `GlideDemoProps`

```typescript
interface GlideDemoProps {
  modelPath?: string;
  config?: Partial<AppConfig>;
  showVisualizer?: boolean;
  scrollContent?: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
}
```

## Data Model / Migrations

No persistent data. All state is in-memory React state/refs.

## Invariants & Failure Modes

| Invariant | Enforcement |
|-----------|-------------|
| Landmarks always 21 points | Guard checks at every entry point |
| Config defaults match YAML | Factory function with hardcoded values, tested |
| Pipeline runs in rAF loop | `requestAnimationFrame`, not `setInterval` |
| State updates throttled | Every 2 frames to avoid React re-render churn |

| Failure Mode | Handling |
|-------------|----------|
| Camera denied | Error state with message |
| No camera found | Error state with message |
| Model load failure | Error state with message |
| Unsupported browser | Error in MediaPipe init |
| Tab hidden | rAF pauses automatically |

## Security / Privacy / Performance notes

- **Privacy**: Camera feed never leaves the browser. All processing is client-side.
- **Model loading**: ~25MB from Google CDN, browser-cached after first load.
- **Performance**: rAF-driven loop. Pipeline objects stored in `useRef` (no recreation). React state updates throttled to every 2-3 frames.
- **No WebWorker**: MediaPipe needs `HTMLVideoElement` DOM access.

## Test Strategy

- **Unit tests**: Pure algorithm functions (scoring, correlation, poses) — 78 tests
- **Cross-validation**: `scripts/generate_test_vectors.py` produces JSON fixtures from Python code
- **Integration**: Not automated (requires camera access)
- **Architecture**: TypeScript strict mode + `noUnusedLocals` enforces type safety

## Open Questions & Risks

- MFC (optical flow) excluded — `mfcScore` hardcoded to 0.5. May need threshold tuning.
- MediaPipe WASM model is ~25MB — first load may be slow on mobile connections.
- `scoreProximityAdjusted` uses `Math.exp` sigmoid instead of `np.exp` — verified identical output.
