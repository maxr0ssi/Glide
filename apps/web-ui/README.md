# Glide Web UI

Browser-based demo of Glide's hand gesture detection algorithms. Runs the full TouchProof detection pipeline in-browser using MediaPipe's WebAssembly hand landmarker.

## Standalone (Dev Server)

```bash
make web-setup   # npm install
make web-dev     # starts Vite at localhost:5173
```

Open in browser, grant camera access. You'll see a split-view with the algorithm visualizer (webcam + landmarks + signal scores) and a scrollable demo area that responds to gestures.

## As a Library (Embeddable Component)

```bash
make web-build   # produces dist/glide-demo.es.js + types
```

```tsx
import { GlideDemo } from '@glide/web-ui';
import '@glide/web-ui/dist/style.css';

function App() {
  return <GlideDemo showVisualizer={true} />;
}
```

### `<GlideDemo />` Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `modelPath` | `string` | Google CDN | Override MediaPipe model URL |
| `config` | `Partial<AppConfig>` | `defaults.yaml` values | Override detection config |
| `showVisualizer` | `boolean` | `true` | Show webcam + signal dashboard |
| `scrollContent` | `ReactNode` | Demo paragraphs | Custom scroll area content |
| `className` | `string` | `''` | Additional CSS class |
| `style` | `CSSProperties` | — | Inline styles |

### `useGlide` Hook

For full control, use the hook directly:

```tsx
import { useGlide } from '@glide/web-ui';

function Custom() {
  const { videoRef, signals, gestureState, landmarks, fps } = useGlide();
  // Build your own UI with the pipeline outputs
}
```

## Testing

```bash
make web-test    # vitest run
```

## Architecture

The TypeScript code mirrors the Python module structure:

| Python | TypeScript | Purpose |
|--------|-----------|---------|
| `glide/core/types.py` | `src/core/types.ts` | GateState, Landmark, HandDet, PoseFlags |
| `glide/core/config_models.py` | `src/core/config.ts` | AppConfig + factory |
| `glide/features/alignment.py` | `src/features/alignment.ts` | HandAligner |
| `glide/features/kinematics.py` | `src/features/kinematics.ts` | KinematicsTracker |
| `glide/features/poses.py` | `src/features/poses.ts` | checkHandPose |
| `glide/gestures/touchproof_scoring.py` | `src/gestures/touchproof-scoring.ts` | Pure scoring functions |
| `glide/gestures/touchproof_detector.py` | `src/gestures/touchproof-detector.ts` | TouchProofDetector |
| `glide/gestures/velocity_tracker.py` | `src/gestures/velocity-tracker.ts` | VelocityTracker |
| `glide/gestures/velocity_controller.py` | `src/gestures/velocity-controller.ts` | VelocityController |

MFC (optical flow) is excluded from the web port — `mfcScore` is hardcoded to 0.5 (neutral).
