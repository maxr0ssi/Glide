/**
 * Pure scoring functions for TouchProof detection.
 * Ported from glide/gestures/touchproof_scoring.py
 *
 * All functions are stateless and side-effect free.
 */

import type { Landmark } from '../core/types';
import type { TouchProofConfig } from '../core/config';

/** Convert normalized distance to proximity score (0-1). */
export function scoreProximity(
  distanceNorm: number,
  enterThreshold: number,
  exitThreshold: number,
): number {
  if (distanceNorm <= enterThreshold) return 1.0;
  if (distanceNorm >= exitThreshold) return 0.0;
  return 1.0 - (distanceNorm - enterThreshold) / (exitThreshold - enterThreshold);
}

/** Convert angle to score (0-1). More parallel = higher. */
export function scoreAngle(angleDeg: number, enterDeg: number, exitDeg: number): number {
  if (angleDeg <= enterDeg) return 1.0;
  if (angleDeg >= exitDeg) return 0.0;
  return 1.0 - (angleDeg - enterDeg) / (exitDeg - enterDeg);
}

/** Score based on visibility asymmetry (occlusion indicator). */
export function scoreVisibility(
  indexTip: Landmark,
  middleTip: Landmark,
  asymmetryMin: number,
): number {
  if (indexTip.visibility == null || middleTip.visibility == null) return 0.5;

  const asymmetry = Math.abs(indexTip.visibility - middleTip.visibility);
  if (asymmetry >= asymmetryMin) return 1.0;
  return asymmetry / asymmetryMin;
}

/** Compute velocity correlation between fingers. */
export function computeCorrelation(
  idxPositions: [number, number][],
  midPositions: [number, number][],
  correlationFrames: number,
  correlationMin: number,
): number {
  if (idxPositions.length < correlationFrames) return 0.5;

  const idxVx: number[] = [];
  const idxVy: number[] = [];
  const midVx: number[] = [];
  const midVy: number[] = [];

  for (let i = 1; i < idxPositions.length; i++) {
    idxVx.push(idxPositions[i]![0] - idxPositions[i - 1]![0]);
    idxVy.push(idxPositions[i]![1] - idxPositions[i - 1]![1]);
    midVx.push(midPositions[i]![0] - midPositions[i - 1]![0]);
    midVy.push(midPositions[i]![1] - midPositions[i - 1]![1]);
  }

  const corrX = pearsonCorrelation(idxVx, midVx);
  const corrY = pearsonCorrelation(idxVy, midVy);

  let avgCorr: number;
  if (corrX != null && corrY != null) {
    avgCorr = (corrX + corrY) / 2;
  } else if (corrX != null) {
    avgCorr = corrX;
  } else if (corrY != null) {
    avgCorr = corrY;
  } else {
    avgCorr = 0.5;
  }

  if (avgCorr >= correlationMin) return 1.0;
  return Math.max(0.0, avgCorr);
}

/** Pearson correlation coefficient. Returns null if cannot compute. */
export function pearsonCorrelation(a: number[], b: number[]): number | null {
  const n = Math.min(a.length, b.length);
  if (n < 2) return null;

  const meanA = a.slice(0, n).reduce((s, x) => s + x, 0) / n;
  const meanB = b.slice(0, n).reduce((s, x) => s + x, 0) / n;

  let varA = 0;
  let varB = 0;
  let cov = 0;

  for (let i = 0; i < n; i++) {
    const dA = a[i]! - meanA;
    const dB = b[i]! - meanB;
    varA += dA * dA;
    varB += dB * dB;
    cov += dA * dB;
  }

  if (varA < 1e-9 || varB < 1e-9) {
    return varA < 1e-9 && varB < 1e-9 ? 1.0 : 0.0;
  }

  return cov / Math.sqrt(varA * varB);
}

/** Score proximity with distance-aware thresholds and relative baseline. */
export function scoreProximityAdjusted(
  distanceNorm: number,
  distanceFactor: number,
  config: TouchProofConfig,
  baseline: number | null,
): number {
  if (config.proximityMode === 'adaptive' && baseline != null) {
    const relativeProximity = baseline / (distanceNorm + 0.001);
    const center = config.relativeTouchThreshold;
    const steepness = 6.0;
    return 1.0 / (1.0 + Math.exp(-steepness * (relativeProximity - center)));
  }

  // Fallback to threshold-based scoring with distance adjustment
  const kD = config.kD;
  const enterAdj = config.proximityEnter * (1 + kD * distanceFactor);
  const exitAdj = config.proximityExit * (1 + kD * distanceFactor);

  if (distanceNorm <= enterAdj) return 1.0;
  if (distanceNorm >= exitAdj) return 0.0;
  return 1.0 - (distanceNorm - enterAdj) / (exitAdj - enterAdj);
}

/** Score angle with distance-aware thresholds. */
export function scoreAngleAdjusted(
  angleDeg: number,
  distanceFactor: number,
  config: TouchProofConfig,
): number {
  const kTheta = config.kTheta;
  const enterAdj = config.angleEnterDeg - kTheta * (1 - distanceFactor);
  const exitAdj = config.angleExitDeg - kTheta * (1 - distanceFactor);

  if (angleDeg <= enterAdj) return 1.0;
  if (angleDeg >= exitAdj) return 0.0;
  return 1.0 - (angleDeg - enterAdj) / (exitAdj - enterAdj);
}

/** Get fusion weights based on hand distance. */
export function getAdaptiveWeights(
  distanceFactor: number,
): { proximity: number; angle: number; mfc: number; occlusion: number } {
  if (distanceFactor > 0.7) {
    return { proximity: 0.45, angle: 0.20, mfc: 0.30, occlusion: 0.05 };
  }
  if (distanceFactor < 0.3) {
    return { proximity: 0.40, angle: 0.30, mfc: 0.25, occlusion: 0.05 };
  }

  const t = (distanceFactor - 0.3) / 0.4;
  const near = { proximity: 0.40, angle: 0.30, mfc: 0.25, occlusion: 0.05 };
  const far = { proximity: 0.45, angle: 0.20, mfc: 0.30, occlusion: 0.05 };

  return {
    proximity: near.proximity * (1 - t) + far.proximity * t,
    angle: near.angle * (1 - t) + far.angle * t,
    mfc: near.mfc * (1 - t) + far.mfc * t,
    occlusion: near.occlusion * (1 - t) + far.occlusion * t,
  };
}
