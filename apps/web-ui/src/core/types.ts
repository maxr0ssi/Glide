/**
 * Core data types for Glide web UI.
 * Ported from glide/core/types.py
 */

export enum GateState {
  UNARMED = 'UNARMED',
  READY = 'READY',
  ARMED = 'ARMED',
  COOLDOWN = 'COOLDOWN',
}

export interface Landmark {
  x: number;
  y: number;
  visibility?: number;
  presence?: number;
}

export interface BBox {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface HandDet {
  landmarks: Landmark[];
  handedness: string;
  confidence: number;
  bbox?: BBox;
}

export interface PoseFlags {
  openPalm: boolean;
  pointingIndex: boolean;
  twoUp: boolean;
}

export function createPoseFlags(): PoseFlags {
  return { openPalm: false, pointingIndex: false, twoUp: false };
}
