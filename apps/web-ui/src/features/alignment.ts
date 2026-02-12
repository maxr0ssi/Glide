/**
 * Hand-aligned coordinate system.
 * Ported from glide/features/alignment.py
 */

import type { Landmark } from '../core/types';

export class HandAligner {
  palmCenter: [number, number] | null = null;
  thetaRad: number | null = null;
  scale: number | null = null;
  imageWidth: number | null = null;
  imageHeight: number | null = null;

  /**
   * Update alignment parameters from hand landmarks.
   * Returns true if successful.
   */
  update(landmarks: Landmark[], imageWidth: number, imageHeight: number): boolean {
    if (!landmarks || landmarks.length < 21) return false;

    this.imageWidth = imageWidth;
    this.imageHeight = imageHeight;

    // Palm center: mean of wrist + MCPs
    const wrist = landmarks[0]!;
    const mcpIndices = [5, 9, 13, 17] as const;
    const palmPoints: [number, number][] = [[wrist.x, wrist.y]];
    for (const i of mcpIndices) {
      palmPoints.push([landmarks[i]!.x, landmarks[i]!.y]);
    }
    const palmX = palmPoints.reduce((s, p) => s + p[0], 0) / palmPoints.length;
    const palmY = palmPoints.reduce((s, p) => s + p[1], 0) / palmPoints.length;
    this.palmCenter = [palmX, palmY];

    // Hand orientation: wrist → middle MCP
    const middleMcp = landmarks[9]!;
    const dx = middleMcp.x - wrist.x;
    const dy = middleMcp.y - wrist.y;
    this.thetaRad = Math.atan2(dy, dx);

    // Scale: index finger length
    const indexTip = landmarks[8]!;
    const indexMcp = landmarks[5]!;
    const fingerLength = Math.hypot(indexTip.x - indexMcp.x, indexTip.y - indexMcp.y);
    this.scale = Math.max(fingerLength, 0.001);

    return true;
  }

  normalizedToPixel(xNorm: number, yNorm: number): [number, number] {
    if (this.imageWidth == null || this.imageHeight == null) return [0, 0];
    return [Math.round(xNorm * this.imageWidth), Math.round(yNorm * this.imageHeight)];
  }

  pixelToNormalized(xPx: number, yPx: number): [number, number] {
    if (this.imageWidth == null || this.imageHeight == null) return [0, 0];
    return [xPx / this.imageWidth, yPx / this.imageHeight];
  }

  /** Transform normalized coordinates to hand-aligned coordinates. */
  toHandAligned(xNorm: number, yNorm: number): [number, number] {
    if (this.palmCenter == null || this.thetaRad == null || this.scale == null) {
      return [0, 0];
    }

    const xRel = xNorm - this.palmCenter[0];
    const yRel = yNorm - this.palmCenter[1];

    const cosTheta = Math.cos(-this.thetaRad);
    const sinTheta = Math.sin(-this.thetaRad);
    const xAligned = cosTheta * xRel - sinTheta * yRel;
    const yAligned = sinTheta * xRel + cosTheta * yRel;

    return [xAligned / this.scale, yAligned / this.scale];
  }

  /** Inverse: hand-aligned → normalized coordinates. */
  fromHandAligned(xAligned: number, yAligned: number): [number, number] {
    if (this.palmCenter == null || this.thetaRad == null || this.scale == null) {
      return [0, 0];
    }

    const xRel = xAligned * this.scale;
    const yRel = yAligned * this.scale;

    const cosTheta = Math.cos(this.thetaRad);
    const sinTheta = Math.sin(this.thetaRad);
    const xNormRel = cosTheta * xRel - sinTheta * yRel;
    const yNormRel = sinTheta * xRel + cosTheta * yRel;

    return [xNormRel + this.palmCenter[0], yNormRel + this.palmCenter[1]];
  }

  /** Get fingertip pixel positions: [[indexX, indexY], [middleX, middleY]]. */
  getFingertipPixels(landmarks: Landmark[]): [[number, number], [number, number]] {
    if (!landmarks || landmarks.length < 21) return [[0, 0], [0, 0]];

    const indexTip = landmarks[8]!;
    const middleTip = landmarks[12]!;

    return [
      this.normalizedToPixel(indexTip.x, indexTip.y),
      this.normalizedToPixel(middleTip.x, middleTip.y),
    ];
  }

  /** Normalized distance between index and middle fingertips (0 = touching). */
  getNormalizedDistance(landmarks: Landmark[]): number {
    if (!landmarks || landmarks.length < 21 || this.scale == null) return Infinity;

    const indexTip = landmarks[8]!;
    const middleTip = landmarks[12]!;

    const idxAligned = this.toHandAligned(indexTip.x, indexTip.y);
    const midAligned = this.toHandAligned(middleTip.x, middleTip.y);

    return Math.hypot(idxAligned[0] - midAligned[0], idxAligned[1] - midAligned[1]);
  }

  /** Log-normalized distance (more stable across camera distances). */
  getNormalizedDistanceLog(landmarks: Landmark[]): number {
    if (!landmarks || landmarks.length < 21) return Infinity;

    const indexTip = landmarks[8]!;
    const middleTip = landmarks[12]!;

    const indexPx = this.normalizedToPixel(indexTip.x, indexTip.y);
    const middlePx = this.normalizedToPixel(middleTip.x, middleTip.y);

    const distancePx = Math.hypot(indexPx[0] - middlePx[0], indexPx[1] - middlePx[1]);
    const referencePx = 30.0;

    return Math.log(1 + distancePx) / Math.log(1 + referencePx);
  }

  /** Angle between index and middle fingers from palm center (degrees). */
  getFingertipAngle(landmarks: Landmark[]): number {
    if (!landmarks || landmarks.length < 21) return 0;

    const indexTip = landmarks[8]!;
    const middleTip = landmarks[12]!;

    const idxAligned = this.toHandAligned(indexTip.x, indexTip.y);
    const midAligned = this.toHandAligned(middleTip.x, middleTip.y);

    const idxLen = Math.hypot(idxAligned[0], idxAligned[1]);
    const midLen = Math.hypot(midAligned[0], midAligned[1]);

    if (idxLen < 1e-6 || midLen < 1e-6) return 0;

    const dot = idxAligned[0] * midAligned[0] + idxAligned[1] * midAligned[1];
    const cosAngle = Math.max(-1, Math.min(1, dot / (idxLen * midLen)));

    return Math.acos(cosAngle) * (180 / Math.PI);
  }

  /** Distance factor: 0.0 = very close, 1.0 = far away. */
  getHandDistanceFactor(): number {
    if (this.scale == null || this.imageWidth == null || this.imageHeight == null) {
      return 0.5;
    }

    const fingerPx = this.scale * Math.max(this.imageWidth, this.imageHeight);
    return Math.max(0, Math.min(1, (200 - fingerPx) / 150));
  }

  /** Finger length in pixels. */
  getFingerLengthPixels(): number {
    if (this.scale == null || this.imageWidth == null || this.imageHeight == null) {
      return 100;
    }
    return this.scale * Math.max(this.imageWidth, this.imageHeight);
  }
}
