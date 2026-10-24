# Glide Web UI

Browser-based demo of Glide's hand gesture detection algorithms. Runs the full TouchProof detection pipeline in-browser using MediaPipe's WebAssembly hand landmarker.

## Standalone (Dev Server)

```bash
make web-setup   # npm install
make web-dev     # starts Vite at localhost:5175
```

Open in browser, grant camera access. You'll see a split-view with the algorithm visualizer (webcam + landmarks + signal scores) and a scrollable demo area that responds to gestures.

## As a Library (Embeddable Component)

Published on npm as [`@maxr0ssi/glide-web-ui`](https://www.npmjs.com/package/@maxr0ssi/glide-web-ui). React 18 is a peer dependency.

```bash
npm install @maxr0ssi/glide-web-ui
```

```tsx
import { GlideDemo } from '@maxr0ssi/glide-web-ui';
import '@maxr0ssi/glide-web-ui/styles';

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
import { useGlide } from '@maxr0ssi/glide-web-ui';

function Custom() {
  const { videoRef, signals, gestureState, landmarks, fps } = useGlide();
  // Build your own UI with the pipeline outputs
}
```

## Testing

```bash
make web-test    # vitest run
make web-lint    # tsc --noEmit + eslint
```

To build the library locally: `npm run build:lib` (writes `dist/glide-demo.{es,cjs}.js`, `dist/glide-web-ui.css` and types).

## Publishing

Publishing is manual: run the **Publish Web UI** workflow (Actions → Publish Web UI → Run workflow) after bumping `version` in `package.json`. It tests, builds and publishes to registry.npmjs.org with provenance. It needs either npm trusted publishing configured for `.github/workflows/publish-web-ui.yml`, or an `NPM_TOKEN` repository secret.

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
