import { describe, it, expect } from 'vitest';
import { HandAligner } from '../../src/features/alignment';
import type { Landmark } from '../../src/core/types';

/** Create 21 fake landmarks in a realistic hand configuration. */
function makeLandmarks(overrides?: Partial<Record<number, Partial<Landmark>>>): Landmark[] {
  // Default: a hand roughly centered, fingers pointing up-right
  const base: Landmark[] = [
    { x: 0.50, y: 0.70 }, // 0: wrist
    { x: 0.48, y: 0.65 }, // 1: thumb CMC
    { x: 0.44, y: 0.60 }, // 2: thumb MCP
    { x: 0.42, y: 0.55 }, // 3: thumb IP
    { x: 0.40, y: 0.50 }, // 4: thumb tip
    { x: 0.48, y: 0.55 }, // 5: index MCP
    { x: 0.47, y: 0.48 }, // 6: index PIP
    { x: 0.46, y: 0.42 }, // 7: index DIP
    { x: 0.45, y: 0.35 }, // 8: index tip
    { x: 0.52, y: 0.54 }, // 9: middle MCP
    { x: 0.52, y: 0.46 }, // 10: middle PIP
    { x: 0.52, y: 0.40 }, // 11: middle DIP
    { x: 0.52, y: 0.33 }, // 12: middle tip
    { x: 0.56, y: 0.56 }, // 13: ring MCP
    { x: 0.57, y: 0.50 }, // 14: ring PIP
    { x: 0.58, y: 0.45 }, // 15: ring DIP
    { x: 0.58, y: 0.40 }, // 16: ring tip
    { x: 0.60, y: 0.60 }, // 17: pinky MCP
    { x: 0.61, y: 0.55 }, // 18: pinky PIP
    { x: 0.62, y: 0.52 }, // 19: pinky DIP
    { x: 0.63, y: 0.50 }, // 20: pinky tip
  ];

  if (overrides) {
    for (const [idx, patch] of Object.entries(overrides)) {
      Object.assign(base[Number(idx)]!, patch);
    }
  }
  return base;
}

describe('HandAligner', () => {
  it('fails update with insufficient landmarks', () => {
    const aligner = new HandAligner();
    expect(aligner.update([], 640, 480)).toBe(false);
    expect(aligner.update([{ x: 0, y: 0 }], 640, 480)).toBe(false);
  });

  it('updates successfully with 21 landmarks', () => {
    const aligner = new HandAligner();
    const lms = makeLandmarks();
    expect(aligner.update(lms, 640, 480)).toBe(true);
    expect(aligner.palmCenter).not.toBeNull();
    expect(aligner.thetaRad).not.toBeNull();
    expect(aligner.scale).toBeGreaterThan(0);
  });

  it('toHandAligned and fromHandAligned are inverses', () => {
    const aligner = new HandAligner();
    aligner.update(makeLandmarks(), 640, 480);

    const [xAligned, yAligned] = aligner.toHandAligned(0.5, 0.4);
    const [xBack, yBack] = aligner.fromHandAligned(xAligned, yAligned);

    expect(xBack).toBeCloseTo(0.5, 4);
    expect(yBack).toBeCloseTo(0.4, 4);
  });

  it('getNormalizedDistance returns small value for touching fingers', () => {
    const aligner = new HandAligner();
    // Move index and middle tips very close together
    const lms = makeLandmarks({
      8: { x: 0.50, y: 0.34 },  // index tip
      12: { x: 0.50, y: 0.34 }, // middle tip same position
    });
    aligner.update(lms, 640, 480);
    const d = aligner.getNormalizedDistance(lms);
    expect(d).toBeLessThan(0.01);
  });

  it('getNormalizedDistance returns larger value for spread fingers', () => {
    const aligner = new HandAligner();
    const lms = makeLandmarks(); // default: fingers spread apart
    aligner.update(lms, 640, 480);
    const d = aligner.getNormalizedDistance(lms);
    expect(d).toBeGreaterThan(0.1);
  });

  it('getFingertipAngle returns 0 for overlapping tips', () => {
    const aligner = new HandAligner();
    const lms = makeLandmarks({
      8: { x: 0.50, y: 0.34 },
      12: { x: 0.50, y: 0.34 },
    });
    aligner.update(lms, 640, 480);
    // Overlapping → angle depends on relation to palm, but should be small
    const angle = aligner.getFingertipAngle(lms);
    expect(angle).toBeLessThan(10);
  });

  it('getHandDistanceFactor returns value in [0, 1]', () => {
    const aligner = new HandAligner();
    aligner.update(makeLandmarks(), 640, 480);
    const df = aligner.getHandDistanceFactor();
    expect(df).toBeGreaterThanOrEqual(0);
    expect(df).toBeLessThanOrEqual(1);
  });

  it('normalizedToPixel converts correctly', () => {
    const aligner = new HandAligner();
    aligner.update(makeLandmarks(), 640, 480);
    const [px, py] = aligner.normalizedToPixel(0.5, 0.5);
    expect(px).toBe(320);
    expect(py).toBe(240);
  });
});
