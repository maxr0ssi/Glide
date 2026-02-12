# Learnings — Web UI TypeScript Port

## What surprised us

- The Python scoring functions ported almost 1:1 to TypeScript. Only 3 NumPy calls needed replacing (`np.log` → `Math.log`, `np.clip` → `Math.max/min`, `np.exp` → `Math.exp`).
- `deque(maxlen=N)` from Python's collections has no browser equivalent — required a custom `BoundedDeque<T>` ring buffer implementation.
- MediaPipe's `@mediapipe/tasks-vision` requires a `HTMLVideoElement` for `detectForVideo()`, so WebWorker offloading is not possible for the detection step.
- Pydantic defaults vs YAML-tuned defaults diverge in several places (e.g., `proximity_enter` Pydantic=0.15 vs YAML=0.25, `angle_enter_deg` Pydantic=20 vs YAML=24). The TS port uses YAML values.

## Decisions made (and why)

- **MFC excluded**: Micro-Flow Cohesion (optical flow) requires OpenCV's `calcOpticalFlowPyrLK` which has no browser equivalent. Hardcoded `mfcScore = 0.5` (neutral). The MFC weight still participates in fusion (~0.125 of fused score), so overall thresholds may need minor tuning.
- **No runtime validation library**: Plain TS interfaces + factory function. Pydantic's validators aren't needed when TypeScript enforces types at compile time. The threshold ordering invariants (enter < exit < hardcap) are enforced by the YAML defaults and tested.
- **rAF instead of setInterval**: `requestAnimationFrame` naturally throttles to display refresh rate and pauses when tab is hidden — avoids wasted compute.
- **React state throttled to every 2 frames**: MediaPipe runs at 30fps but React re-renders for signal display don't need every frame.

## Follow-ups

- Test with real camera to validate detection accuracy without MFC signal.
- Consider bumping `fusedEnterThreshold` by ~0.05 if false positives increase without MFC.
- Library build (`vite build --mode lib`) needs testing with an external React app consumer.

### PATCH SUMMARY
- Mode: Doing
- Changed files:
  - apps/web-ui/ (new: 27 files — src, tests, config)
  - scripts/generate_test_vectors.py (new)
  - docs/designs/web-ui/DESIGN.md (new)
  - docs/learnings/2026-02-12-web-ui-port.md (new)
  - .gitignore (modified: added web-ui ignores)
  - Makefile (modified: added web-* targets)
  - docs/DEPENDENCIES.md (modified: added web-ui section)
  - CHANGELOG.md (modified: added web-ui entry)
  - .github/workflows/ci.yml (modified: added web-ui job)
- Why: Port Glide gesture detection to browser for web demo + embeddable component
- How: Direct TypeScript port of Python algorithms; MediaPipe WASM for hand detection; React for UI
- Tests: 78 unit tests across 10 test files, all passing. Cross-validated against Python fixtures.
- Risks & Mitigations: MFC excluded (hardcoded to neutral) — may need threshold tuning after real-world testing.
