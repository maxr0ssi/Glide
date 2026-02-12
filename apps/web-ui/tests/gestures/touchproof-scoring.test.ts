import { describe, it, expect } from 'vitest';
import {
  scoreProximity,
  scoreAngle,
  scoreVisibility,
  pearsonCorrelation,
  computeCorrelation,
  scoreProximityAdjusted,
  scoreAngleAdjusted,
  getAdaptiveWeights,
} from '../../src/gestures/touchproof-scoring';
import { createDefaultConfig } from '../../src/core/config';

describe('scoreProximity', () => {
  it('returns 1.0 when distance <= enter threshold', () => {
    expect(scoreProximity(0.1, 0.25, 0.40)).toBe(1.0);
    expect(scoreProximity(0.25, 0.25, 0.40)).toBe(1.0);
  });

  it('returns 0.0 when distance >= exit threshold', () => {
    expect(scoreProximity(0.40, 0.25, 0.40)).toBe(0.0);
    expect(scoreProximity(0.50, 0.25, 0.40)).toBe(0.0);
  });

  it('linearly interpolates between thresholds', () => {
    const score = scoreProximity(0.325, 0.25, 0.40);
    expect(score).toBeCloseTo(0.5, 2);
  });
});

describe('scoreAngle', () => {
  it('returns 1.0 when angle <= enter', () => {
    expect(scoreAngle(10, 24, 32)).toBe(1.0);
  });

  it('returns 0.0 when angle >= exit', () => {
    expect(scoreAngle(40, 24, 32)).toBe(0.0);
  });

  it('interpolates between thresholds', () => {
    expect(scoreAngle(28, 24, 32)).toBeCloseTo(0.5, 2);
  });
});

describe('scoreVisibility', () => {
  it('returns 0.5 when no visibility data', () => {
    expect(scoreVisibility({ x: 0, y: 0 }, { x: 0, y: 0 }, 0.12)).toBe(0.5);
  });

  it('returns 1.0 when asymmetry >= min', () => {
    expect(
      scoreVisibility(
        { x: 0, y: 0, visibility: 0.9 },
        { x: 0, y: 0, visibility: 0.7 },
        0.12,
      ),
    ).toBe(1.0);
  });

  it('returns proportional score for partial asymmetry', () => {
    const score = scoreVisibility(
      { x: 0, y: 0, visibility: 0.9 },
      { x: 0, y: 0, visibility: 0.84 },
      0.12,
    );
    expect(score).toBeCloseTo(0.5, 1);
  });
});

describe('pearsonCorrelation', () => {
  it('returns null for < 2 samples', () => {
    expect(pearsonCorrelation([], [])).toBeNull();
    expect(pearsonCorrelation([1], [2])).toBeNull();
  });

  it('returns 1.0 for perfectly correlated', () => {
    expect(pearsonCorrelation([1, 2, 3, 4], [2, 4, 6, 8])).toBeCloseTo(1.0, 6);
  });

  it('returns -1.0 for perfectly anti-correlated', () => {
    expect(pearsonCorrelation([1, 2, 3, 4], [8, 6, 4, 2])).toBeCloseTo(-1.0, 6);
  });

  it('returns 1.0 for both constant (zero variance)', () => {
    expect(pearsonCorrelation([5, 5, 5], [3, 3, 3])).toBe(1.0);
  });

  it('returns 0.0 for one constant (asymmetric variance)', () => {
    expect(pearsonCorrelation([1, 2, 3], [5, 5, 5])).toBe(0.0);
  });
});

describe('computeCorrelation', () => {
  it('returns 0.5 (neutral) when insufficient data', () => {
    expect(computeCorrelation([], [], 5, 0.7)).toBe(0.5);
  });

  it('returns high score for correlated movement', () => {
    const idx: [number, number][] = Array.from({ length: 6 }, (_, i) => [i * 0.01, i * 0.02]);
    const mid: [number, number][] = Array.from({ length: 6 }, (_, i) => [i * 0.01, i * 0.02]);
    const score = computeCorrelation(idx, mid, 5, 0.7);
    expect(score).toBe(1.0);
  });
});

describe('scoreProximityAdjusted', () => {
  const cfg = createDefaultConfig().touchproof;

  it('uses adaptive mode with baseline', () => {
    const score = scoreProximityAdjusted(0.1, 0.5, cfg, 0.3);
    expect(score).toBeGreaterThan(0.5);
  });

  it('falls back to threshold when no baseline', () => {
    const score = scoreProximityAdjusted(0.1, 0.5, cfg, null);
    expect(score).toBe(1.0); // Well within adjusted enter threshold
  });
});

describe('scoreAngleAdjusted', () => {
  const cfg = createDefaultConfig().touchproof;

  it('returns 1.0 for small angle', () => {
    expect(scoreAngleAdjusted(5, 0.5, cfg)).toBe(1.0);
  });

  it('returns 0.0 for large angle', () => {
    expect(scoreAngleAdjusted(50, 0.5, cfg)).toBe(0.0);
  });
});

describe('getAdaptiveWeights', () => {
  it('returns far weights for high distance factor', () => {
    const w = getAdaptiveWeights(0.9);
    expect(w.proximity).toBe(0.45);
    expect(w.angle).toBe(0.20);
  });

  it('returns near weights for low distance factor', () => {
    const w = getAdaptiveWeights(0.1);
    expect(w.proximity).toBe(0.40);
    expect(w.angle).toBe(0.30);
  });

  it('weights sum to 1.0', () => {
    for (const df of [0.0, 0.3, 0.5, 0.7, 1.0]) {
      const w = getAdaptiveWeights(df);
      const sum = w.proximity + w.angle + w.mfc + w.occlusion;
      expect(sum).toBeCloseTo(1.0, 6);
    }
  });
});
