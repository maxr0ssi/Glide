import { describe, it, expect } from 'vitest';
import { VelocityTracker, vec2dMagnitude, vec2dZero } from '../../src/gestures/velocity-tracker';

describe('vec2d helpers', () => {
  it('vec2dMagnitude computes correctly', () => {
    expect(vec2dMagnitude({ x: 3, y: 4 })).toBe(5);
    expect(vec2dMagnitude(vec2dZero())).toBe(0);
  });
});

describe('VelocityTracker', () => {
  it('returns null when not touching', () => {
    const tracker = new VelocityTracker();
    const v = tracker.update([0.5, 0.5], [0.5, 0.5], false, 0);
    expect(v).toBeNull();
  });

  it('returns null for single sample', () => {
    const tracker = new VelocityTracker();
    const v = tracker.update([0.5, 0.5], [0.5, 0.5], true, 0);
    expect(v).toBeNull();
  });

  it('returns velocity for multiple samples', () => {
    const tracker = new VelocityTracker(200);
    tracker.update([0.5, 0.5], [0.5, 0.5], true, 0);
    const v = tracker.update([0.5, 0.6], [0.5, 0.6], true, 50);
    expect(v).not.toBeNull();
    // Moving downward (positive y in normalized coords)
    expect(v!.y).toBeGreaterThan(0);
  });

  it('resets on touch end', () => {
    const tracker = new VelocityTracker(200);
    tracker.update([0.5, 0.5], [0.5, 0.5], true, 0);
    tracker.update([0.5, 0.6], [0.5, 0.6], true, 50);
    tracker.update([0.5, 0.6], [0.5, 0.6], false, 100); // release
    const v = tracker.update([0.5, 0.5], [0.5, 0.5], true, 150);
    expect(v).toBeNull(); // Only 1 sample after reset
  });

  it('removes old samples outside window', () => {
    const tracker = new VelocityTracker(100);
    tracker.update([0.5, 0.5], [0.5, 0.5], true, 0);
    tracker.update([0.5, 0.5], [0.5, 0.5], true, 50);
    tracker.update([0.5, 0.6], [0.5, 0.6], true, 200); // samples at 0 and 50 should be pruned
    const v = tracker.update([0.5, 0.7], [0.5, 0.7], true, 250);
    expect(v).not.toBeNull();
  });
});
