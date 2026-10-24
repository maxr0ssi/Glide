/**
 * Camera lifecycle tests for useGlide: tracks must stop on unmount even
 * though React has detached videoRef by then, late getUserMedia results
 * must be stopped, and the frame loop must not outlive the component.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { act, StrictMode, type RefObject } from 'react';
import { createRoot, type Root } from 'react-dom/client';

// --- Fake MediaPipe detector -------------------------------------------------
const { detectors, FakeDetector } = vi.hoisted(() => {
  const detectors: Array<InstanceType<typeof FakeDetector>> = [];
  class FakeDetector {
    isReady = false;
    destroyed = false;
    resolveInit: () => void = () => {};
    constructor() {
      detectors.push(this);
    }
    initialize() {
      return new Promise<void>((resolve) => {
        this.resolveInit = () => {
          if (!this.destroyed) this.isReady = true;
          resolve();
        };
      });
    }
    detect() {
      return null;
    }
    destroy() {
      this.destroyed = true;
      this.isReady = false;
    }
  }
  return { detectors, FakeDetector };
});
vi.mock('../../src/perception/hand-detector', () => ({ WebHandDetector: FakeDetector }));

import { useGlide, type UseGlideReturn } from '../../src/hooks/useGlide';
import { CAMERA_MESSAGES } from '../../src/perception/camera-errors';

// --- Fake getUserMedia -------------------------------------------------------
interface FakeTrack { readyState: 'live' | 'ended'; stop: () => void }
const tracks: FakeTrack[] = [];
let pendingGum: Array<{ resolve: () => void; reject: (e: unknown) => void }> = [];

function fakeStream(): MediaStream {
  const t: FakeTrack = { readyState: 'live', stop() { this.readyState = 'ended'; } };
  tracks.push(t);
  return { getTracks: () => [t] } as unknown as MediaStream;
}
const liveTracks = () => tracks.filter((t) => t.readyState === 'live').length;

// --- Manual requestAnimationFrame -------------------------------------------
let rafQueue = new Map<number, FrameRequestCallback>();
let rafNext = 1;
function flushFrames(n = 1) {
  for (let i = 0; i < n; i++) {
    const q = rafQueue;
    rafQueue = new Map();
    q.forEach((cb) => cb(performance.now()));
  }
}

let latest: UseGlideReturn | null = null;
function Harness() {
  const g = useGlide();
  latest = g;
  return <video ref={g.videoRef as RefObject<HTMLVideoElement>} />;
}

let container: HTMLDivElement;
let root: Root;

beforeEach(() => {
  (globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
  detectors.length = 0;
  tracks.length = 0;
  pendingGum = [];
  rafQueue = new Map();
  latest = null;

  Object.defineProperty(navigator, 'mediaDevices', {
    configurable: true,
    value: {
      getUserMedia: vi.fn(
        () =>
          new Promise<MediaStream>((resolve, reject) => {
            pendingGum.push({ resolve: () => resolve(fakeStream()), reject });
          }),
      ),
    },
  });
  vi.spyOn(HTMLMediaElement.prototype, 'play').mockResolvedValue(undefined);
  vi.spyOn(HTMLMediaElement.prototype, 'pause').mockImplementation(() => {});
  vi.stubGlobal('requestAnimationFrame', (cb: FrameRequestCallback) => {
    const id = rafNext++;
    rafQueue.set(id, cb);
    return id;
  });
  vi.stubGlobal('cancelAnimationFrame', (id: number) => rafQueue.delete(id));

  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
});

afterEach(() => {
  act(() => root.unmount());
  container.remove();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

const flush = () => act(async () => { await Promise.resolve(); });

async function resolveAllGum() {
  await act(async () => {
    pendingGum.forEach((p) => p.resolve());
    pendingGum = [];
  });
}

describe('useGlide camera cleanup', () => {
  it('stops tracks and detaches srcObject on unmount after the camera started', async () => {
    act(() => root.render(<Harness />));
    await resolveAllGum();
    const video = container.querySelector('video')!;
    expect(liveTracks()).toBe(1);
    expect(video.srcObject).not.toBeNull();

    act(() => root.unmount());
    expect(liveTracks()).toBe(0);
    expect(video.srcObject).toBeNull();
    root = createRoot(container);
  });

  it('stops a stream that resolves after unmount', async () => {
    act(() => root.render(<Harness />));
    expect(pendingGum.length).toBe(1);
    act(() => root.unmount());
    await resolveAllGum();
    expect(tracks.length).toBe(1);
    expect(liveTracks()).toBe(0);
    root = createRoot(container);
  });

  it('leaves exactly one live stream under StrictMode and none after unmount', async () => {
    act(() => root.render(<StrictMode><Harness /></StrictMode>));
    await resolveAllGum();
    expect(tracks.length).toBe(2);
    expect(liveTracks()).toBe(1);

    act(() => root.unmount());
    expect(liveTracks()).toBe(0);
    root = createRoot(container);
  });

  it('stops the frame loop and releases a detector that finishes loading after unmount', async () => {
    act(() => root.render(<Harness />));
    await resolveAllGum();
    await flush();
    const det = detectors[detectors.length - 1]!;
    await act(async () => det.resolveInit());
    expect(latest!.isReady).toBe(true);
    expect(rafQueue.size).toBe(1);
    flushFrames(3);
    expect(rafQueue.size).toBe(1);

    act(() => root.unmount());
    expect(rafQueue.size).toBe(0);
    expect(det.destroyed).toBe(true);
    root = createRoot(container);

    // Detector still loading when the component goes away.
    act(() => root.render(<Harness />));
    await resolveAllGum();
    await flush();
    const late = detectors[detectors.length - 1]!;
    act(() => root.unmount());
    await act(async () => late.resolveInit());
    expect(late.destroyed).toBe(true);
    expect(late.isReady).toBe(false);
    expect(rafQueue.size).toBe(0);
    expect(liveTracks()).toBe(0);
    root = createRoot(container);
  });

  it('survives 10 mount/unmount cycles without leaking tracks', async () => {
    for (let i = 0; i < 10; i++) {
      act(() => root.render(<Harness />));
      if (i % 2 === 0) await resolveAllGum(); // odd cycles unmount before the camera resolves
      act(() => root.unmount());
      await resolveAllGum();
      expect(liveTracks()).toBe(0);
      root = createRoot(container);
    }
  });
});

describe('useGlide camera errors', () => {
  const failWith = async (name: string) => {
    act(() => root.render(<Harness />));
    await act(async () => {
      pendingGum.forEach((p) => p.reject(new DOMException('x', name)));
      pendingGum = [];
    });
    return latest!.error;
  };

  it('reports a user denial', async () => {
    expect(await failWith('NotAllowedError')).toBe(CAMERA_MESSAGES.denied);
  });

  it('reports a Permissions-Policy block', async () => {
    Object.defineProperty(document, 'featurePolicy', {
      configurable: true,
      value: { allowsFeature: () => false },
    });
    try {
      expect(await failWith('NotAllowedError')).toBe(CAMERA_MESSAGES.unavailable);
    } finally {
      delete (document as { featurePolicy?: unknown }).featurePolicy;
    }
  });

  it('reports no device and device in use', async () => {
    expect(await failWith('NotFoundError')).toBe(CAMERA_MESSAGES.notFound);
    act(() => root.unmount());
    root = createRoot(container);
    expect(await failWith('NotReadableError')).toBe(CAMERA_MESSAGES.inUse);
  });

  it('reports a missing camera API', async () => {
    Object.defineProperty(navigator, 'mediaDevices', { configurable: true, value: undefined });
    act(() => root.render(<Harness />));
    await flush();
    expect(latest!.error).toBe(CAMERA_MESSAGES.unavailable);
  });
});
