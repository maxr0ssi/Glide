/**
 * MediaPipe hand detection wrapper for browser.
 * Uses @mediapipe/tasks-vision HandLandmarker.
 */

import { HandLandmarker, FilesetResolver } from '@mediapipe/tasks-vision';
import type { HandDet, Landmark } from '../core/types';

const DEFAULT_MODEL_URL =
  'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task';

const DEFAULT_WASM_PATH =
  'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.32/wasm';

export interface WebHandDetectorOptions {
  modelPath?: string;
  wasmPath?: string;
  numHands?: number;
  minDetectionConfidence?: number;
  minTrackingConfidence?: number;
}

export class WebHandDetector {
  private landmarker: HandLandmarker | null = null;
  private _ready = false;

  get isReady(): boolean {
    return this._ready;
  }

  async initialize(options?: WebHandDetectorOptions): Promise<void> {
    const wasmPath = options?.wasmPath ?? DEFAULT_WASM_PATH;
    const modelPath = options?.modelPath ?? DEFAULT_MODEL_URL;

    const vision = await FilesetResolver.forVisionTasks(wasmPath);

    this.landmarker = await HandLandmarker.createFromOptions(vision, {
      baseOptions: {
        modelAssetPath: modelPath,
        delegate: 'GPU',
      },
      runningMode: 'VIDEO',
      numHands: options?.numHands ?? 1,
      minHandDetectionConfidence: options?.minDetectionConfidence ?? 0.5,
      minTrackingConfidence: options?.minTrackingConfidence ?? 0.5,
    });

    this._ready = true;
  }

  detect(video: HTMLVideoElement, timestampMs: number): HandDet | null {
    if (!this.landmarker) return null;

    const result = this.landmarker.detectForVideo(video, timestampMs);

    if (!result.landmarks || result.landmarks.length === 0) return null;

    const mpLandmarks = result.landmarks[0]!;
    const handedness = result.handednesses?.[0]?.[0]?.categoryName ?? 'Right';
    const confidence = result.handednesses?.[0]?.[0]?.score ?? 0;

    const landmarks: Landmark[] = mpLandmarks.map((lm) => ({
      x: lm.x,
      y: lm.y,
      visibility: lm.visibility ?? undefined,
    }));

    return {
      landmarks,
      handedness,
      confidence,
    };
  }

  destroy(): void {
    this.landmarker?.close();
    this.landmarker = null;
    this._ready = false;
  }
}
