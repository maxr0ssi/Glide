/**
 * TouchProof signals data structure.
 * Ported from glide/gestures/touchproof_signals.py (dataclass only; MicroFlowTracker excluded).
 */

export interface TouchProofSignals {
  proximityScore: number;  // 0-1 (closer = higher)
  angleScore: number;      // 0-1 (more parallel = higher)
  correlationScore: number; // 0-1 (moving together = higher)
  visibilityScore: number;  // 0-1 (asymmetry = higher)
  mfcScore: number;         // 0-1 (hardcoded to 0.5 — no optical flow in web)
  distanceFactor: number;   // 0-1 (0=close, 1=far)
  fusedScore: number;       // 0-1 (overall confidence)
  isTouching: boolean;      // Final decision
}

export function emptySignals(): TouchProofSignals {
  return {
    proximityScore: 0,
    angleScore: 0,
    correlationScore: 0,
    visibilityScore: 0,
    mfcScore: 0,
    distanceFactor: 0.5,
    fusedScore: 0,
    isTouching: false,
  };
}
