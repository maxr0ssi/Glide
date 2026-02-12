/**
 * Velocity tracking for smooth scrolling gestures.
 * Ported from glide/gestures/velocity_tracker.py
 */

export interface Vec2D {
  x: number;
  y: number;
}

export function vec2dMagnitude(v: Vec2D): number {
  return Math.sqrt(v.x * v.x + v.y * v.y);
}

export function vec2dZero(): Vec2D {
  return { x: 0, y: 0 };
}

interface PositionSample {
  x: number;
  y: number;
  timestampMs: number;
}

export class VelocityTracker {
  private windowMs: number;
  private smoothingFactor: number;
  private samples: PositionSample[] = [];
  private lastVelocity: Vec2D | null = null;
  private minSamples = 2;
  private noiseThreshold = 0.5;

  constructor(windowMs = 100, smoothingFactor = 0.3) {
    this.windowMs = windowMs;
    this.smoothingFactor = smoothingFactor;
  }

  update(
    indexTip: [number, number],
    middleTip: [number, number],
    isTouching: boolean,
    timestampMs: number,
  ): Vec2D | null {
    if (!isTouching) {
      this.reset();
      return null;
    }

    const midX = (indexTip[0] + middleTip[0]) / 2;
    const midY = (indexTip[1] + middleTip[1]) / 2;

    this.samples.push({ x: midX, y: midY, timestampMs });

    // Remove old samples outside window
    const cutoff = timestampMs - this.windowMs;
    while (this.samples.length > 0 && this.samples[0]!.timestampMs < cutoff) {
      this.samples.shift();
    }

    if (this.samples.length < this.minSamples) return null;

    let velocity = this._calculateVelocity();

    // Apply EMA smoothing
    if (this.lastVelocity && velocity) {
      velocity = {
        x: this.smoothingFactor * velocity.x + (1 - this.smoothingFactor) * this.lastVelocity.x,
        y: this.smoothingFactor * velocity.y + (1 - this.smoothingFactor) * this.lastVelocity.y,
      };
    }

    this.lastVelocity = velocity;
    return velocity;
  }

  private _calculateVelocity(): Vec2D | null {
    if (this.samples.length < 2) return null;

    const first = this.samples[0]!;
    const last = this.samples[this.samples.length - 1]!;

    const dtMs = last.timestampMs - first.timestampMs;
    if (dtMs <= 0) return null;

    let vx = (last.x - first.x) * 1000 / dtMs;
    let vy = (last.y - first.y) * 1000 / dtMs;

    if (Math.abs(vx) < this.noiseThreshold / 1000) vx = 0;
    if (Math.abs(vy) < this.noiseThreshold / 1000) vy = 0;

    return { x: vx, y: vy };
  }

  reset(): void {
    this.samples = [];
    this.lastVelocity = null;
  }
}
