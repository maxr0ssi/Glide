/**
 * BoundedDeque — fixed-capacity ring buffer replacing Python's deque(maxlen=N).
 */
export class BoundedDeque<T> {
  private _buf: T[];
  private _head: number;
  private _size: number;
  private _capacity: number;

  constructor(capacity: number) {
    if (capacity < 1) throw new RangeError('capacity must be >= 1');
    this._capacity = capacity;
    this._buf = new Array<T>(capacity);
    this._head = 0;
    this._size = 0;
  }

  get length(): number {
    return this._size;
  }

  get capacity(): number {
    return this._capacity;
  }

  push(item: T): void {
    const idx = (this._head + this._size) % this._capacity;
    this._buf[idx] = item;
    if (this._size < this._capacity) {
      this._size++;
    } else {
      this._head = (this._head + 1) % this._capacity;
    }
  }

  at(index: number): T {
    if (index < 0 || index >= this._size) {
      throw new RangeError(`index ${index} out of range [0, ${this._size})`);
    }
    return this._buf[(this._head + index) % this._capacity]!;
  }

  /** Access from end: -1 = last, -2 = second to last, etc. */
  fromEnd(offset: number): T {
    if (offset >= 0 || -offset > this._size) {
      throw new RangeError(`offset ${offset} out of range`);
    }
    return this.at(this._size + offset);
  }

  first(): T | undefined {
    return this._size > 0 ? this.at(0) : undefined;
  }

  last(): T | undefined {
    return this._size > 0 ? this.at(this._size - 1) : undefined;
  }

  clear(): void {
    this._head = 0;
    this._size = 0;
  }

  toArray(): T[] {
    const result: T[] = [];
    for (let i = 0; i < this._size; i++) {
      result.push(this.at(i));
    }
    return result;
  }

  *[Symbol.iterator](): Iterator<T> {
    for (let i = 0; i < this._size; i++) {
      yield this.at(i);
    }
  }
}
