/**
 * Velocity-based scroll controller.
 * Ported from glide/gestures/velocity_controller.py
 */

import type { Vec2D } from './velocity-tracker';
import { vec2dZero, vec2dMagnitude } from './velocity-tracker';

export enum GestureState {
  IDLE = 'idle',
  SCROLLING = 'scrolling',
}

export interface VelocityUpdate {
  velocity: Vec2D;
  state: GestureState;
  isActive: boolean;
}

export class VelocityController {
  private minVelocity: number;
  private scrollDelayMs: number;
  state: GestureState = GestureState.IDLE;
  private wasTouching = false;
  private touchStartMs: number | null = null;

  constructor(minVelocity = 0.001, scrollDelayMs = 200) {
    this.minVelocity = minVelocity;
    this.scrollDelayMs = scrollDelayMs;
  }

  update(
    velocity: Vec2D | null,
    isTouching: boolean,
    isHighFive: boolean,
    timestampMs: number,
  ): VelocityUpdate {
    if (isHighFive) {
      this.state = GestureState.IDLE;
      this.touchStartMs = null;
      return { velocity: vec2dZero(), state: this.state, isActive: false };
    }

    if (this.state === GestureState.IDLE) {
      if (isTouching && velocity && vec2dMagnitude(velocity) > this.minVelocity) {
        if (this.touchStartMs == null) {
          this.touchStartMs = timestampMs;
        }
        if (timestampMs - this.touchStartMs >= this.scrollDelayMs) {
          this.state = GestureState.SCROLLING;
        }
      } else if (!isTouching) {
        this.touchStartMs = null;
      }
    } else if (this.state === GestureState.SCROLLING) {
      if (!isTouching && this.wasTouching) {
        this.state = GestureState.IDLE;
        this.touchStartMs = null;
      }
    }

    this.wasTouching = isTouching;

    return {
      velocity: velocity ?? vec2dZero(),
      state: this.state,
      isActive: this.state === GestureState.SCROLLING && isTouching,
    };
  }
}
