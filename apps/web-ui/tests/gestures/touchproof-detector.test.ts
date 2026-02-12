import { describe, it, expect } from 'vitest';
import { TouchProofDetector } from '../../src/gestures/touchproof-detector';
import { createDefaultConfig } from '../../src/core/config';
import { GateState } from '../../src/core/types';
import type { Landmark } from '../../src/core/types';

function makeLandmarks(
  indexTipPos: [number, number] = [0.45, 0.35],
  middleTipPos: [number, number] = [0.52, 0.33],
): Landmark[] {
  return [
    { x: 0.50, y: 0.70 }, // 0: wrist
    { x: 0.48, y: 0.65 }, // 1
    { x: 0.44, y: 0.60 }, // 2
    { x: 0.42, y: 0.55 }, // 3
    { x: 0.40, y: 0.50 }, // 4
    { x: 0.48, y: 0.55 }, // 5: index MCP
    { x: 0.47, y: 0.48 }, // 6
    { x: 0.46, y: 0.42 }, // 7
    { x: indexTipPos[0], y: indexTipPos[1], visibility: 0.9 }, // 8: index tip
    { x: 0.52, y: 0.54 }, // 9: middle MCP
    { x: 0.52, y: 0.46 }, // 10
    { x: 0.52, y: 0.40 }, // 11
    { x: middleTipPos[0], y: middleTipPos[1], visibility: 0.9 }, // 12: middle tip
    { x: 0.56, y: 0.56 }, // 13: ring MCP
    { x: 0.57, y: 0.50 }, // 14
    { x: 0.58, y: 0.45 }, // 15
    { x: 0.58, y: 0.40 }, // 16
    { x: 0.60, y: 0.60 }, // 17: pinky MCP
    { x: 0.61, y: 0.55 }, // 18
    { x: 0.62, y: 0.52 }, // 19
    { x: 0.63, y: 0.50 }, // 20
  ];
}

describe('TouchProofDetector', () => {
  it('starts in UNARMED state', () => {
    const detector = new TouchProofDetector(createDefaultConfig().touchproof);
    expect(detector.state).toBe(GateState.UNARMED);
  });

  it('returns not-touching for spread fingers', () => {
    const detector = new TouchProofDetector(createDefaultConfig().touchproof);
    const signals = detector.update(
      makeLandmarks([0.35, 0.30], [0.60, 0.30]),
      640,
      480,
    );
    expect(signals.isTouching).toBe(false);
    expect(signals.fusedScore).toBeLessThan(0.5);
  });

  it('transitions to READY after enough frames of touching', () => {
    const cfg = createDefaultConfig().touchproof;
    const detector = new TouchProofDetector(cfg);

    // Touching position: tips very close
    const touchingLms = makeLandmarks([0.50, 0.34], [0.50, 0.34]);

    let touching = false;
    // Feed multiple frames of touching signal
    for (let i = 0; i < cfg.framesToEnter + 5; i++) {
      const signals = detector.update(touchingLms, 640, 480);
      if (signals.isTouching) {
        touching = true;
        break;
      }
    }

    expect(touching).toBe(true);
    expect(detector.state).toBe(GateState.READY);
  });

  it('returns empty signals for empty landmarks', () => {
    const detector = new TouchProofDetector(createDefaultConfig().touchproof);
    const signals = detector.update([], 640, 480);
    expect(signals.isTouching).toBe(false);
    expect(signals.fusedScore).toBe(0);
  });

  it('triggers hard cap on extreme proximity', () => {
    const detector = new TouchProofDetector(createDefaultConfig().touchproof);
    // Fingers very far apart
    const signals = detector.update(
      makeLandmarks([0.20, 0.20], [0.80, 0.80]),
      640,
      480,
    );
    expect(signals.fusedScore).toBe(0);
    expect(signals.isTouching).toBe(false);
  });
});
