import { describe, it, expect } from 'vitest';
import {
  CAMERA_MESSAGES,
  cameraAllowedByPolicy,
  cameraApiAvailable,
  describeCameraError,
} from '../../src/perception/camera-errors';

const domErr = (name: string, message = '') => Object.assign(new Error(message), { name });

describe('describeCameraError', () => {
  it('NotAllowedError with camera allowed by policy is a user denial', () => {
    expect(describeCameraError(domErr('NotAllowedError', 'Permission denied'), true)).toBe(
      CAMERA_MESSAGES.denied,
    );
  });

  it('NotAllowedError when the policy check is unavailable is a user denial', () => {
    expect(describeCameraError(domErr('NotAllowedError'), undefined)).toBe(CAMERA_MESSAGES.denied);
  });

  it('NotAllowedError with camera blocked by Permissions-Policy is unavailable', () => {
    expect(describeCameraError(domErr('NotAllowedError'), false)).toBe(CAMERA_MESSAGES.unavailable);
  });

  it('SecurityError is unavailable', () => {
    expect(describeCameraError(domErr('SecurityError'), true)).toBe(CAMERA_MESSAGES.unavailable);
  });

  it('NotFoundError is no device', () => {
    expect(describeCameraError(domErr('NotFoundError'), true)).toBe(CAMERA_MESSAGES.notFound);
    expect(describeCameraError(domErr('DevicesNotFoundError'), true)).toBe(CAMERA_MESSAGES.notFound);
  });

  it('NotReadableError is in use', () => {
    expect(describeCameraError(domErr('NotReadableError'), true)).toBe(CAMERA_MESSAGES.inUse);
  });

  it('works with DOMException', () => {
    expect(describeCameraError(new DOMException('x', 'NotReadableError'), true)).toBe(
      CAMERA_MESSAGES.inUse,
    );
  });

  it('returns null for unrelated errors', () => {
    expect(describeCameraError(new Error('model failed'), true)).toBeNull();
    expect(describeCameraError('string', true)).toBeNull();
    expect(describeCameraError(null, true)).toBeNull();
  });

  it('keeps messages short', () => {
    for (const m of Object.values(CAMERA_MESSAGES)) expect(m.length).toBeLessThanOrEqual(90);
  });
});

describe('cameraAllowedByPolicy', () => {
  it('reads document.featurePolicy.allowsFeature', () => {
    const doc = (allows: boolean) =>
      ({ featurePolicy: { allowsFeature: (f: string) => (f === 'camera' ? allows : true) } }) as unknown as Document;
    expect(cameraAllowedByPolicy(doc(false))).toBe(false);
    expect(cameraAllowedByPolicy(doc(true))).toBe(true);
  });

  it('is undefined when the API is missing', () => {
    expect(cameraAllowedByPolicy({} as Document)).toBeUndefined();
    expect(cameraAllowedByPolicy(undefined)).toBeUndefined();
  });
});

describe('cameraApiAvailable', () => {
  it('detects a missing mediaDevices (insecure context)', () => {
    expect(cameraApiAvailable({} as Navigator)).toBe(false);
    expect(
      cameraApiAvailable({ mediaDevices: { getUserMedia: () => Promise.resolve() } } as unknown as Navigator),
    ).toBe(true);
  });
});
