import { describe, it, expect } from 'vitest';
import { VelocityController, GestureState } from '../../src/gestures/velocity-controller';

describe('VelocityController', () => {
  it('starts in IDLE state', () => {
    const ctrl = new VelocityController();
    expect(ctrl.state).toBe(GestureState.IDLE);
  });

  it('stays IDLE when not touching', () => {
    const ctrl = new VelocityController();
    const update = ctrl.update({ x: 1, y: 1 }, false, false, 0);
    expect(update.state).toBe(GestureState.IDLE);
    expect(update.isActive).toBe(false);
  });

  it('waits for scroll delay before transitioning to SCROLLING', () => {
    const ctrl = new VelocityController(0.001, 200);
    // First touch — still within delay
    const u1 = ctrl.update({ x: 0, y: 0.5 }, true, false, 0);
    expect(u1.state).toBe(GestureState.IDLE);

    // Still within delay
    const u2 = ctrl.update({ x: 0, y: 0.5 }, true, false, 100);
    expect(u2.state).toBe(GestureState.IDLE);

    // Past delay — now scrolling
    const u3 = ctrl.update({ x: 0, y: 0.5 }, true, false, 250);
    expect(u3.state).toBe(GestureState.SCROLLING);
    expect(u3.isActive).toBe(true);
  });

  it('stays IDLE when touching but velocity below threshold', () => {
    const ctrl = new VelocityController(1.0);
    const update = ctrl.update({ x: 0, y: 0.0001 }, true, false, 0);
    expect(update.state).toBe(GestureState.IDLE);
  });

  it('stops SCROLLING when touch releases', () => {
    const ctrl = new VelocityController(0.001, 0); // no delay for this test
    ctrl.update({ x: 0, y: 0.5 }, true, false, 0); // Start scrolling
    const update = ctrl.update({ x: 0, y: 0 }, false, false, 100); // Release
    expect(update.state).toBe(GestureState.IDLE);
  });

  it('high-five always stops scrolling', () => {
    const ctrl = new VelocityController(0.001, 0);
    ctrl.update({ x: 0, y: 0.5 }, true, false, 0); // Start scrolling
    const update = ctrl.update({ x: 0, y: 0.5 }, true, true, 100); // High five
    expect(update.state).toBe(GestureState.IDLE);
    expect(update.isActive).toBe(false);
  });

  it('returns zero velocity when no velocity provided', () => {
    const ctrl = new VelocityController();
    const update = ctrl.update(null, false, false, 0);
    expect(update.velocity.x).toBe(0);
    expect(update.velocity.y).toBe(0);
  });
});
