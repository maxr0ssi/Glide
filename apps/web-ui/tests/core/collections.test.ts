import { describe, it, expect } from 'vitest';
import { BoundedDeque } from '../../src/core/collections';

describe('BoundedDeque', () => {
  it('starts empty', () => {
    const d = new BoundedDeque<number>(5);
    expect(d.length).toBe(0);
    expect(d.capacity).toBe(5);
    expect(d.first()).toBeUndefined();
    expect(d.last()).toBeUndefined();
  });

  it('pushes items up to capacity', () => {
    const d = new BoundedDeque<number>(3);
    d.push(1);
    d.push(2);
    d.push(3);
    expect(d.length).toBe(3);
    expect(d.at(0)).toBe(1);
    expect(d.at(2)).toBe(3);
  });

  it('evicts oldest when at capacity', () => {
    const d = new BoundedDeque<number>(3);
    d.push(1);
    d.push(2);
    d.push(3);
    d.push(4); // evicts 1
    expect(d.length).toBe(3);
    expect(d.at(0)).toBe(2);
    expect(d.at(1)).toBe(3);
    expect(d.at(2)).toBe(4);
  });

  it('supports fromEnd access', () => {
    const d = new BoundedDeque<string>(5);
    d.push('a');
    d.push('b');
    d.push('c');
    expect(d.fromEnd(-1)).toBe('c');
    expect(d.fromEnd(-2)).toBe('b');
    expect(d.fromEnd(-3)).toBe('a');
  });

  it('throws on out-of-range access', () => {
    const d = new BoundedDeque<number>(3);
    d.push(1);
    expect(() => d.at(1)).toThrow(RangeError);
    expect(() => d.at(-1)).toThrow(RangeError);
    expect(() => d.fromEnd(0)).toThrow(RangeError);
    expect(() => d.fromEnd(-2)).toThrow(RangeError);
  });

  it('clears properly', () => {
    const d = new BoundedDeque<number>(3);
    d.push(1);
    d.push(2);
    d.clear();
    expect(d.length).toBe(0);
    expect(d.first()).toBeUndefined();
  });

  it('converts to array', () => {
    const d = new BoundedDeque<number>(3);
    d.push(10);
    d.push(20);
    d.push(30);
    d.push(40);
    expect(d.toArray()).toEqual([20, 30, 40]);
  });

  it('is iterable', () => {
    const d = new BoundedDeque<number>(3);
    d.push(1);
    d.push(2);
    d.push(3);
    d.push(4);
    expect([...d]).toEqual([2, 3, 4]);
  });

  it('throws on invalid capacity', () => {
    expect(() => new BoundedDeque(0)).toThrow(RangeError);
  });
});
