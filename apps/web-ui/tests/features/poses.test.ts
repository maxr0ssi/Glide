import { describe, it, expect } from 'vitest';
import { checkHandPose } from '../../src/features/poses';
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
    { x: 0.58, y: 0.40 }, // 16: ring tip
    { x: 0.60, y: 0.60 }, // 17: pinky MCP
    { x: 0.61, y: 0.55 }, // 18
    { x: 0.62, y: 0.52 }, // 19
    { x: 0.63, y: 0.50 }, // 20
  ];
}

describe('checkHandPose', () => {
  it('returns all-false for empty landmarks', () => {
    const flags = checkHandPose([]);
    expect(flags.openPalm).toBe(false);
    expect(flags.pointingIndex).toBe(false);
    expect(flags.twoUp).toBe(false);
  });

  it('detects open palm when spread > 0.12', () => {
    const lms = makeLandmarks();
    // index MCP x=0.48, pinky MCP x=0.60 → spread=0.12 → exactly at boundary
    const flags = checkHandPose(lms);
    // abs(0.48 - 0.60) = 0.12, needs > 0.12
    expect(flags.openPalm).toBe(false);

    // Increase spread
    lms[17] = { x: 0.65, y: 0.60 }; // spread = 0.17
    const flags2 = checkHandPose(lms);
    expect(flags2.openPalm).toBe(true);
  });

  it('detects pointing index when index tip above middle tip', () => {
    const lms = makeLandmarks();
    // index tip y=0.35, middle tip y=0.33 → index_tip.y < middle_tip.y - 0.02?
    // 0.35 < 0.33 - 0.02 = 0.31? No
    const flags = checkHandPose(lms);
    expect(flags.pointingIndex).toBe(false);

    // Make index tip higher (smaller y)
    lms[8] = { x: 0.45, y: 0.28 }; // now 0.28 < 0.33 - 0.02 = 0.31
    const flags2 = checkHandPose(lms);
    expect(flags2.pointingIndex).toBe(true);
  });

  it('detects two-up when both index and middle above ring', () => {
    const lms = makeLandmarks();
    // index y=0.35, middle y=0.33, ring y=0.40
    // 0.35 < 0.40-0.02=0.38? Yes. 0.33 < 0.38? Yes.
    const flags = checkHandPose(lms);
    expect(flags.twoUp).toBe(true);
  });
});
