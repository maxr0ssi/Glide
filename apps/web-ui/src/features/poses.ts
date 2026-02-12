/**
 * Hand pose detection.
 * Ported from glide/features/poses.py
 */

import type { Landmark, PoseFlags } from '../core/types';
import { createPoseFlags } from '../core/types';

/**
 * Check hand pose for common gestures.
 *
 * - openPalm: spread between index MCP and pinky MCP is large
 * - pointingIndex: index tip beyond middle tip in pointing direction
 * - twoUp: index and middle tips above ring tip (y smaller in image coords)
 */
export function checkHandPose(landmarks: Landmark[]): PoseFlags {
  const flags = createPoseFlags();
  if (!landmarks || landmarks.length < 21) return flags;

  const indexMcp = landmarks[5]!;
  const pinkyMcp = landmarks[17]!;
  const indexTip = landmarks[8]!;
  const middleTip = landmarks[12]!;
  const ringTip = landmarks[16]!;

  const spread = Math.abs(indexMcp.x - pinkyMcp.x);
  flags.openPalm = spread > 0.12;

  flags.pointingIndex = indexTip.y < middleTip.y - 0.02;

  flags.twoUp = indexTip.y < ringTip.y - 0.02 && middleTip.y < ringTip.y - 0.02;

  return flags;
}
