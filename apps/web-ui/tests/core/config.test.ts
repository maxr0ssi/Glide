import { describe, it, expect } from 'vitest';
import { createDefaultConfig, mergeConfig } from '../../src/core/config';

describe('createDefaultConfig', () => {
  it('returns config with YAML-tuned defaults', () => {
    const cfg = createDefaultConfig();

    expect(cfg.frameWidth).toBe(960);
    expect(cfg.mirror).toBe(true);

    // Verify YAML-tuned touchproof values (differ from Pydantic defaults)
    expect(cfg.touchproof.proximityEnter).toBe(0.25);
    expect(cfg.touchproof.proximityExit).toBe(0.40);
    expect(cfg.touchproof.angleEnterDeg).toBe(24.0);
    expect(cfg.touchproof.angleExitDeg).toBe(32.0);
    expect(cfg.touchproof.kTheta).toBe(2.0);
    expect(cfg.touchproof.framesToEnter).toBe(4);
    expect(cfg.touchproof.fusedEnterThreshold).toBe(0.75);
    expect(cfg.touchproof.fusedExitThreshold).toBe(0.65);

    // Kinematics
    expect(cfg.kinematics.emaAlpha).toBe(0.35);
    expect(cfg.kinematics.bufferFrames).toBe(24);

    // Scroll
    expect(cfg.scroll.pixelsPerDegree).toBe(5.0);
  });
});

describe('mergeConfig', () => {
  it('deep-merges overrides without losing defaults', () => {
    const cfg = mergeConfig({
      touchproof: { proximityEnter: 0.1 } as never,
    });

    expect(cfg.touchproof.proximityEnter).toBe(0.1);
    // Other touchproof defaults preserved
    expect(cfg.touchproof.proximityExit).toBe(0.40);
    expect(cfg.touchproof.angleEnterDeg).toBe(24.0);

    // Other top-level defaults preserved
    expect(cfg.frameWidth).toBe(960);
    expect(cfg.kinematics.emaAlpha).toBe(0.35);
  });

  it('returns defaults when given empty overrides', () => {
    const cfg = mergeConfig({});
    const def = createDefaultConfig();
    expect(cfg).toEqual(def);
  });
});
