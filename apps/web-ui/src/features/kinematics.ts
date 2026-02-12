/**
 * Kinematics tracking — EMA-smoothed fingertip positions.
 * Ported from glide/features/kinematics.py
 */

import { BoundedDeque } from '../core/collections';
import type { Landmark } from '../core/types';

export interface HandKinematics {
  palmX: number;
  palmY: number;
  thetaRad: number;
  indexTipRel: [number, number];
  middleTipRel: [number, number] | null;
  fingerLengthIdx: number;
  fingerLengthMid: number | null;
}

export class KinematicsTracker {
  private emaAlpha: number;
  private _idxTipEma: [number, number] | null = null;
  private _midTipEma: [number, number] | null = null;

  trail: BoundedDeque<[number, number]>;
  trailMid: BoundedDeque<[number, number]>;
  trailMean: BoundedDeque<[number, number]>;

  constructor(emaAlpha = 0.35, bufferFrames = 24) {
    this.emaAlpha = emaAlpha;
    this.trail = new BoundedDeque(bufferFrames);
    this.trailMid = new BoundedDeque(bufferFrames);
    this.trailMean = new BoundedDeque(bufferFrames);
  }

  private static mean(points: [number, number][]): [number, number] {
    const n = Math.max(points.length, 1);
    const sx = points.reduce((s, p) => s + p[0], 0);
    const sy = points.reduce((s, p) => s + p[1], 0);
    return [sx / n, sy / n];
  }

  private static rot(px: number, py: number, theta: number): [number, number] {
    const c = Math.cos(theta);
    const s = Math.sin(theta);
    return [c * px - s * py, s * px + c * py];
  }

  private static ema(
    prev: [number, number] | null,
    cur: [number, number],
    alpha: number,
  ): [number, number] {
    if (prev == null) return cur;
    return [alpha * cur[0] + (1 - alpha) * prev[0], alpha * cur[1] + (1 - alpha) * prev[1]];
  }

  compute(landmarks: Landmark[]): HandKinematics | null {
    if (!landmarks || landmarks.length < 21) return null;

    const wrist = landmarks[0]!;
    const mcps = [landmarks[5]!, landmarks[9]!, landmarks[13]!, landmarks[17]!];
    const [palmX, palmY] = KinematicsTracker.mean([
      [wrist.x, wrist.y],
      ...mcps.map((m): [number, number] => [m.x, m.y]),
    ]);

    const midMcp = landmarks[9]!;
    const theta = Math.atan2(midMcp.y - wrist.y, midMcp.x - wrist.x);

    const idxTip = landmarks[8]!;
    const midTip = landmarks[12]!;
    const idxMcp = landmarks[5]!;
    const midMcpLmk = landmarks[9]!;

    // Hand-aligned, palm-relative
    const idxRel: [number, number] = [idxTip.x - palmX, idxTip.y - palmY];
    const midRel: [number, number] = [midTip.x - palmX, midTip.y - palmY];
    const idxRelAligned = KinematicsTracker.rot(idxRel[0], idxRel[1], -theta);
    const midRelAligned = KinematicsTracker.rot(midRel[0], midRel[1], -theta);

    // EMA smoothing
    this._idxTipEma = KinematicsTracker.ema(this._idxTipEma, idxRelAligned, this.emaAlpha);
    this._midTipEma = KinematicsTracker.ema(this._midTipEma, midRelAligned, this.emaAlpha);

    // Finger lengths
    const fingerLenIdx = Math.hypot(idxTip.x - idxMcp.x, idxTip.y - idxMcp.y);
    const fingerLenMid = Math.hypot(midTip.x - midMcpLmk.x, midTip.y - midMcpLmk.y);

    // Update trails
    this.trail.push(this._idxTipEma);
    this.trailMid.push(this._midTipEma);

    const meanX = (this._idxTipEma[0] + this._midTipEma[0]) / 2;
    const meanY = (this._idxTipEma[1] + this._midTipEma[1]) / 2;
    this.trailMean.push([meanX, meanY]);

    return {
      palmX,
      palmY,
      thetaRad: theta,
      indexTipRel: this._idxTipEma,
      middleTipRel: this._midTipEma,
      fingerLengthIdx: fingerLenIdx,
      fingerLengthMid: fingerLenMid,
    };
  }

  getMeanFingertip(): [number, number] | null {
    if (this._idxTipEma == null || this._midTipEma == null) return null;
    return [
      (this._idxTipEma[0] + this._midTipEma[0]) / 2,
      (this._idxTipEma[1] + this._midTipEma[1]) / 2,
    ];
  }

  getFingerSpeeds(lookback = 1): [number | null, number | null] {
    let idxSpeed: number | null = null;
    let midSpeed: number | null = null;

    if (this.trail.length > lookback) {
      const cur = this.trail.fromEnd(-1);
      const prev = this.trail.fromEnd(-(lookback + 1));
      idxSpeed = Math.hypot(cur[0] - prev[0], cur[1] - prev[1]);
    }

    if (this.trailMid.length > lookback) {
      const cur = this.trailMid.fromEnd(-1);
      const prev = this.trailMid.fromEnd(-(lookback + 1));
      midSpeed = Math.hypot(cur[0] - prev[0], cur[1] - prev[1]);
    }

    return [idxSpeed, midSpeed];
  }
}
