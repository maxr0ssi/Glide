/**
 * TouchProof detector — multi-signal fusion for fingertip contact detection.
 * Ported from glide/gestures/touchproof_detector.py
 *
 * MFC (optical flow) is excluded: mfcScore hardcoded to 0.5 (neutral).
 */

import type { TouchProofConfig } from '../core/config';
import { GateState } from '../core/types';
import type { Landmark } from '../core/types';
import { BoundedDeque } from '../core/collections';
import { HandAligner } from '../features/alignment';
import {
  scoreProximity,
  scoreAngle,
  scoreVisibility,
  computeCorrelation,
  scoreProximityAdjusted,
  scoreAngleAdjusted,
  getAdaptiveWeights,
} from './touchproof-scoring';
import type { TouchProofSignals } from './touchproof-signals';
import { emptySignals } from './touchproof-signals';

export class TouchProofDetector {
  config: TouchProofConfig;
  aligner: HandAligner;
  state: GateState = GateState.UNARMED;

  private _enterCounter = 0;
  private _exitCounter = 0;

  private _idxPositions: BoundedDeque<[number, number]>;
  private _midPositions: BoundedDeque<[number, number]>;

  private _proximityEma: number | null = null;
  private _angleEma: number | null = null;

  private _baselineClose: number | null = null;
  private _baselineFar: number | null = null;
  private _baselineAlpha: number;

  /** Hardcoded MFC score (no optical flow in browser). */
  private _lastMfcScore = 0.5;

  constructor(config: TouchProofConfig) {
    this.config = config;
    this.aligner = new HandAligner();
    this._idxPositions = new BoundedDeque(config.correlationFrames + 1);
    this._midPositions = new BoundedDeque(config.correlationFrames + 1);
    this._baselineAlpha = config.baselineLearningRate;
  }

  /**
   * Update touch detection with new landmarks.
   * Note: no frame_bgr param (MFC excluded).
   */
  update(
    landmarks: Landmark[],
    imageWidth: number,
    imageHeight: number,
  ): TouchProofSignals {
    if (!this.aligner.update(landmarks, imageWidth, imageHeight)) {
      return emptySignals();
    }

    if (landmarks.length < 21) return emptySignals();

    const indexTip = landmarks[8]!;
    const middleTip = landmarks[12]!;

    // 1. PROXIMITY
    const proximityNorm =
      this.config.proximityMode === 'logarithmic'
        ? this.aligner.getNormalizedDistanceLog(landmarks)
        : this.aligner.getNormalizedDistance(landmarks);

    // Hard cap
    if (proximityNorm > this.config.proximityHardCap) {
      return {
        proximityScore: 0,
        angleScore: 0,
        correlationScore: 0,
        visibilityScore: 0,
        mfcScore: 0,
        distanceFactor: this.aligner.getHandDistanceFactor(),
        fusedScore: 0,
        isTouching: false,
      };
    }

    const proximityScoreRaw = scoreProximity(
      proximityNorm,
      this.config.proximityEnter,
      this.config.proximityExit,
    );

    let proximityScore: number;
    if (this.config.smoothProximity) {
      if (this._proximityEma == null) {
        this._proximityEma = proximityScoreRaw;
      } else {
        this._proximityEma =
          this.config.emaAlpha * proximityScoreRaw +
          (1 - this.config.emaAlpha) * this._proximityEma;
      }
      proximityScore = this._proximityEma;
    } else {
      proximityScore = proximityScoreRaw;
    }

    // 2. ANGLE
    const angleDeg = this.aligner.getFingertipAngle(landmarks);

    if (angleDeg > this.config.angleHardCapDeg) {
      return {
        proximityScore,
        angleScore: 0,
        correlationScore: 0,
        visibilityScore: 0,
        mfcScore: 0,
        distanceFactor: this.aligner.getHandDistanceFactor(),
        fusedScore: 0,
        isTouching: false,
      };
    }

    // Angle smoothing
    const angleAlpha = 0.2;
    if (this._angleEma == null) {
      this._angleEma = angleDeg;
    } else {
      this._angleEma = angleAlpha * angleDeg + (1 - angleAlpha) * this._angleEma;
    }

    // Raw angle score computed for consistency with Python;
    // the adjusted version (scoreAngleAdjusted) is used in fusion below.
    scoreAngle(
      this._angleEma,
      this.config.angleEnterDeg,
      this.config.angleExitDeg,
    );

    // 3. CORRELATION
    const idxAligned = this.aligner.toHandAligned(indexTip.x, indexTip.y);
    const midAligned = this.aligner.toHandAligned(middleTip.x, middleTip.y);
    this._idxPositions.push(idxAligned);
    this._midPositions.push(midAligned);

    const correlationScore = computeCorrelation(
      this._idxPositions.toArray(),
      this._midPositions.toArray(),
      this.config.correlationFrames,
      this.config.correlationMin,
    );

    // 4. VISIBILITY
    const visibilityScore = scoreVisibility(
      indexTip,
      middleTip,
      this.config.visibilityAsymmetryMin,
    );

    // 5. DISTANCE FACTOR
    const distanceFactor = this.aligner.getHandDistanceFactor();

    // 6. BASELINE UPDATE
    this._updateBaseline(proximityNorm, distanceFactor);

    // 7. MFC (hardcoded — no optical flow in browser)
    const mfcScore = this._lastMfcScore;

    // 8. DISTANCE-AWARE FUSION
    const weights = getAdaptiveWeights(distanceFactor);
    const baseline = this._getBaselineDistance(distanceFactor);

    const proximityScoreAdj = scoreProximityAdjusted(
      proximityNorm,
      distanceFactor,
      this.config,
      baseline,
    );
    const angleScoreAdj = scoreAngleAdjusted(angleDeg, distanceFactor, this.config);

    const fusedScore =
      weights.proximity * proximityScoreAdj +
      weights.angle * angleScoreAdj +
      weights.mfc * mfcScore +
      weights.occlusion * visibilityScore;

    // STATE MACHINE
    const isTouching = this._updateState(fusedScore);

    return {
      proximityScore: proximityScoreAdj,
      angleScore: angleScoreAdj,
      correlationScore,
      visibilityScore,
      mfcScore,
      distanceFactor,
      fusedScore,
      isTouching,
    };
  }

  private _updateState(fusedScore: number): boolean {
    if (this.state === GateState.UNARMED) {
      if (fusedScore > this.config.fusedEnterThreshold) {
        this._enterCounter++;
        if (this._enterCounter >= this.config.framesToEnter) {
          this.state = GateState.READY;
          this._enterCounter = 0;
          return true;
        }
      } else {
        this._enterCounter = 0;
      }
      return false;
    }

    if (this.state === GateState.READY) {
      if (fusedScore < this.config.fusedExitThreshold) {
        this._exitCounter++;
        if (this._exitCounter >= this.config.framesToExit) {
          this.state = GateState.UNARMED;
          this._exitCounter = 0;
          return false;
        }
      } else {
        this._exitCounter = 0;
      }
      return true;
    }

    return false;
  }

  private _updateBaseline(distanceNorm: number, distanceFactor: number): void {
    if (this.state !== GateState.UNARMED) return;

    if (distanceFactor < 0.3) {
      if (this._baselineClose == null) {
        this._baselineClose = distanceNorm;
      } else {
        this._baselineClose =
          this._baselineAlpha * distanceNorm + (1 - this._baselineAlpha) * this._baselineClose;
      }
    } else if (distanceFactor > 0.7) {
      if (this._baselineFar == null) {
        this._baselineFar = distanceNorm;
      } else {
        this._baselineFar =
          this._baselineAlpha * distanceNorm + (1 - this._baselineAlpha) * this._baselineFar;
      }
    }
  }

  private _getBaselineDistance(distanceFactor: number): number | null {
    if (this._baselineClose == null || this._baselineFar == null) return null;

    if (distanceFactor < 0.3) return this._baselineClose;
    if (distanceFactor > 0.7) return this._baselineFar;

    const t = (distanceFactor - 0.3) / 0.4;
    return this._baselineClose * (1 - t) + this._baselineFar * t;
  }
}
