/**
 * Map getUserMedia failures to short, actionable messages.
 *
 * NotAllowedError covers two different situations: the user (or their
 * browser settings) denied the camera, or the page's Permissions-Policy
 * blocks it. Only the first is something the user can fix, so they get
 * different messages.
 */

export const CAMERA_MESSAGES = {
  denied: "Camera access was blocked. Allow it in your browser's site settings, then try again.",
  unavailable: "The camera isn't available on this page.",
  notFound: 'No camera found. Connect one, then try again.',
  inUse: 'The camera is in use by another app. Close it, then try again.',
} as const;

interface FeaturePolicyLike {
  allowsFeature?: (feature: string) => boolean;
}

/**
 * Whether the page's Permissions-Policy allows the camera.
 * Returns undefined when the browser doesn't expose the check.
 */
export function cameraAllowedByPolicy(doc: Document | undefined = globalThis.document): boolean | undefined {
  try {
    const policy = (doc as (Document & { featurePolicy?: FeaturePolicyLike }) | undefined)?.featurePolicy;
    const allows = policy?.allowsFeature?.('camera');
    return typeof allows === 'boolean' ? allows : undefined;
  } catch {
    return undefined;
  }
}

/** Whether getUserMedia can be called at all in this context. */
export function cameraApiAvailable(nav: Navigator | undefined = globalThis.navigator): boolean {
  return typeof nav?.mediaDevices?.getUserMedia === 'function';
}

/**
 * Return a message for a camera error, or null when the error is not a
 * recognised camera failure (the caller then falls back to its own message).
 */
export function describeCameraError(
  err: unknown,
  policyAllowsCamera: boolean | undefined = cameraAllowedByPolicy(),
): string | null {
  const name = typeof err === 'object' && err !== null && 'name' in err
    ? String((err as { name: unknown }).name)
    : '';

  switch (name) {
    case 'NotAllowedError':
    case 'PermissionDeniedError': // legacy Chrome name
      return policyAllowsCamera === false ? CAMERA_MESSAGES.unavailable : CAMERA_MESSAGES.denied;
    case 'SecurityError':
      return CAMERA_MESSAGES.unavailable;
    case 'NotFoundError':
    case 'DevicesNotFoundError': // legacy Chrome name
    case 'OverconstrainedError':
      return CAMERA_MESSAGES.notFound;
    case 'NotReadableError':
    case 'TrackStartError': // legacy Chrome name
      return CAMERA_MESSAGES.inUse;
    default:
      return null;
  }
}
