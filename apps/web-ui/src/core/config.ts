/**
 * Configuration models for Glide web UI.
 * Ported from glide/core/config_models.py + configs/defaults.yaml
 *
 * Uses plain TS interfaces + factory function (no runtime validation library).
 * Default values come from configs/defaults.yaml where they differ from Pydantic defaults.
 */

export interface GatesConfig {
  presenceConf: number;
  poses: string[];
  preStillMs: number;
  maxIdleRmsSpeed: number;
}

export interface KinematicsConfig {
  emaAlpha: number;
  bufferFrames: number;
  frameLookback: number;
}

export interface ScrollConfig {
  enabled: boolean;
  pixelsPerDegree: number;
  maxVelocity: number;
  accelerationCurve: number;
}

export interface TouchProofConfig {
  // Proximity thresholds (normalized)
  proximityEnter: number;
  proximityExit: number;
  proximityHardCap: number;

  // Angle thresholds (degrees)
  angleEnterDeg: number;
  angleExitDeg: number;
  angleHardCapDeg: number;

  // Motion correlation
  correlationFrames: number;
  correlationMin: number;

  // Visibility/occlusion
  visibilityAsymmetryMin: number;

  // Temporal stability
  framesToEnter: number;
  framesToExit: number;

  // Fused score thresholds
  fusedEnterThreshold: number;
  fusedExitThreshold: number;

  // Signal smoothing
  emaAlpha: number;
  smoothProximity: boolean;

  // Proximity scoring mode
  proximityMode: 'fixed' | 'adaptive' | 'logarithmic';
  baselineLearningRate: number;
  relativeTouchThreshold: number;

  // Distance interaction parameters
  distanceNearPx: number;
  distanceFarPx: number;
  kD: number;
  kTheta: number;

  // MFC parameters (kept for weight structure even though MFC is hardcoded)
  mfcWindowFrames: number;
  mfcPatchSize: number;
  mfcCorrMin: number;
  mfcMagRatioMin: number;
  mfcMagRatioMax: number;
}

export interface AppConfig {
  cameraIndex: number;
  frameWidth: number;
  mirror: boolean;
  touchThresholdPixels: number;

  gates: GatesConfig;
  kinematics: KinematicsConfig;
  touchproof: TouchProofConfig;
  scroll: ScrollConfig;
}

/** Create default config matching configs/defaults.yaml tuned values. */
export function createDefaultConfig(): AppConfig {
  return {
    cameraIndex: 0,
    frameWidth: 960,
    mirror: true,
    touchThresholdPixels: 50,

    gates: {
      presenceConf: 0.7,
      poses: ['open_palm', 'pointing_index', 'two_up'],
      preStillMs: 150,
      maxIdleRmsSpeed: 0.08,
    },

    kinematics: {
      emaAlpha: 0.35,
      bufferFrames: 24,
      frameLookback: 5,
    },

    touchproof: {
      proximityEnter: 0.25,
      proximityExit: 0.40,
      proximityHardCap: 0.50,

      angleEnterDeg: 24.0,
      angleExitDeg: 32.0,
      angleHardCapDeg: 45.0,

      correlationFrames: 5,
      correlationMin: 0.70,

      visibilityAsymmetryMin: 0.12,

      framesToEnter: 4,
      framesToExit: 3,

      fusedEnterThreshold: 0.75,
      fusedExitThreshold: 0.65,

      emaAlpha: 0.3,
      smoothProximity: true,

      proximityMode: 'adaptive',
      baselineLearningRate: 0.02,
      relativeTouchThreshold: 0.85,

      distanceNearPx: 200,
      distanceFarPx: 50,
      kD: 0.30,
      kTheta: 2.0,

      mfcWindowFrames: 5,
      mfcPatchSize: 15,
      mfcCorrMin: 0.70,
      mfcMagRatioMin: 0.6,
      mfcMagRatioMax: 1.4,
    },

    scroll: {
      enabled: true,
      pixelsPerDegree: 5.0,
      maxVelocity: 100.0,
      accelerationCurve: 1.5,
    },
  };
}

/** Deep-merge a partial config over defaults. */
export function mergeConfig(overrides: Partial<AppConfig>): AppConfig {
  const base = createDefaultConfig();
  return {
    ...base,
    ...overrides,
    gates: { ...base.gates, ...overrides.gates },
    kinematics: { ...base.kinematics, ...overrides.kinematics },
    touchproof: { ...base.touchproof, ...overrides.touchproof },
    scroll: { ...base.scroll, ...overrides.scroll },
  };
}
