import { describe, it, expect } from 'vitest';
import { GateState, createPoseFlags } from '../../src/core/types';
import type { Landmark, HandDet, BBox } from '../../src/core/types';

describe('GateState', () => {
  it('has all expected values', () => {
    expect(GateState.UNARMED).toBe('UNARMED');
    expect(GateState.READY).toBe('READY');
    expect(GateState.ARMED).toBe('ARMED');
    expect(GateState.COOLDOWN).toBe('COOLDOWN');
  });
});

describe('Landmark', () => {
  it('can be created with required fields', () => {
    const lm: Landmark = { x: 0.5, y: 0.3 };
    expect(lm.x).toBe(0.5);
    expect(lm.y).toBe(0.3);
    expect(lm.visibility).toBeUndefined();
  });

  it('can include optional visibility and presence', () => {
    const lm: Landmark = { x: 0.1, y: 0.2, visibility: 0.9, presence: 0.8 };
    expect(lm.visibility).toBe(0.9);
    expect(lm.presence).toBe(0.8);
  });
});

describe('HandDet', () => {
  it('can be created with required fields', () => {
    const det: HandDet = {
      landmarks: [{ x: 0, y: 0 }],
      handedness: 'Right',
      confidence: 0.95,
    };
    expect(det.landmarks).toHaveLength(1);
    expect(det.bbox).toBeUndefined();
  });

  it('can include optional bbox', () => {
    const bbox: BBox = { x: 10, y: 20, w: 100, h: 100 };
    const det: HandDet = {
      landmarks: [],
      handedness: 'Left',
      confidence: 0.8,
      bbox,
    };
    expect(det.bbox?.w).toBe(100);
  });
});

describe('createPoseFlags', () => {
  it('returns all-false defaults', () => {
    const flags = createPoseFlags();
    expect(flags.openPalm).toBe(false);
    expect(flags.pointingIndex).toBe(false);
    expect(flags.twoUp).toBe(false);
  });
});
