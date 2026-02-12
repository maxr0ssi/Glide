import { describe, it, expect } from 'vitest';
import { KinematicsTracker } from '../../src/features/kinematics';
import type { Landmark } from '../../src/core/types';

function makeLandmarks(): Landmark[] {
  return [
    { x: 0.50, y: 0.70 }, // 0: wrist
    { x: 0.48, y: 0.65 }, // 1
    { x: 0.44, y: 0.60 }, // 2
    { x: 0.42, y: 0.55 }, // 3
    { x: 0.40, y: 0.50 }, // 4
    { x: 0.48, y: 0.55 }, // 5: index MCP
    { x: 0.47, y: 0.48 }, // 6
    { x: 0.46, y: 0.42 }, // 7
    { x: 0.45, y: 0.35 }, // 8: index tip
    { x: 0.52, y: 0.54 }, // 9: middle MCP
    { x: 0.52, y: 0.46 }, // 10
    { x: 0.52, y: 0.40 }, // 11
    { x: 0.52, y: 0.33 }, // 12: middle tip
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

describe('KinematicsTracker', () => {
  it('returns null for insufficient landmarks', () => {
    const tracker = new KinematicsTracker();
    expect(tracker.compute([])).toBeNull();
    expect(tracker.compute([{ x: 0, y: 0 }])).toBeNull();
  });

  it('computes hand kinematics from valid landmarks', () => {
    const tracker = new KinematicsTracker();
    const k = tracker.compute(makeLandmarks());
    expect(k).not.toBeNull();
    expect(k!.palmX).toBeGreaterThan(0);
    expect(k!.palmY).toBeGreaterThan(0);
    expect(typeof k!.thetaRad).toBe('number');
    expect(k!.fingerLengthIdx).toBeGreaterThan(0);
    expect(k!.fingerLengthMid).toBeGreaterThan(0);
  });

  it('applies EMA smoothing across frames', () => {
    const tracker = new KinematicsTracker(0.5);
    const lms = makeLandmarks();

    const k1 = tracker.compute(lms);

    // Shift index tip slightly
    lms[8] = { x: 0.46, y: 0.36 };
    const k2 = tracker.compute(lms);

    // EMA smoothing: second result should be between first frame values and shifted values
    expect(k2!.indexTipRel[0]).not.toBe(k1!.indexTipRel[0]);
  });

  it('tracks trail positions', () => {
    const tracker = new KinematicsTracker(0.5, 10);
    const lms = makeLandmarks();

    tracker.compute(lms);
    tracker.compute(lms);
    tracker.compute(lms);

    expect(tracker.trail.length).toBe(3);
    expect(tracker.trailMid.length).toBe(3);
    expect(tracker.trailMean.length).toBe(3);
  });

  it('getMeanFingertip returns null before first compute', () => {
    const tracker = new KinematicsTracker();
    expect(tracker.getMeanFingertip()).toBeNull();
  });

  it('getMeanFingertip returns value after compute', () => {
    const tracker = new KinematicsTracker();
    tracker.compute(makeLandmarks());
    const mean = tracker.getMeanFingertip();
    expect(mean).not.toBeNull();
    expect(mean!).toHaveLength(2);
  });

  it('getFingerSpeeds returns null initially, value after frames', () => {
    const tracker = new KinematicsTracker(0.5, 10);
    const lms = makeLandmarks();

    tracker.compute(lms);
    const [s1] = tracker.getFingerSpeeds(1);
    expect(s1).toBeNull();

    // Move tip
    lms[8] = { x: 0.46, y: 0.36 };
    tracker.compute(lms);
    const [s2] = tracker.getFingerSpeeds(1);
    expect(s2).not.toBeNull();
    expect(s2!).toBeGreaterThan(0);
  });
});
