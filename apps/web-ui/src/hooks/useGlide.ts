/**
 * useGlide — core orchestration hook for the Glide gesture pipeline.
 *
 * Manages: getUserMedia → MediaPipe → alignment → kinematics → poses →
 *          touchproof → velocity → scroll signals
 */

import { useRef, useState, useEffect, useCallback } from 'react';
import type { Landmark } from '../core/types';
import type { AppConfig } from '../core/config';
import { createDefaultConfig, mergeConfig } from '../core/config';
import { KinematicsTracker } from '../features/kinematics';
import { checkHandPose } from '../features/poses';
import { TouchProofDetector } from '../gestures/touchproof-detector';
import type { TouchProofSignals } from '../gestures/touchproof-signals';
import { emptySignals } from '../gestures/touchproof-signals';
import { VelocityTracker } from '../gestures/velocity-tracker';
import type { Vec2D } from '../gestures/velocity-tracker';
import { VelocityController, GestureState } from '../gestures/velocity-controller';
import { WebHandDetector } from '../perception/hand-detector';
import {
  CAMERA_MESSAGES,
  cameraApiAvailable,
  describeCameraError,
} from '../perception/camera-errors';

export interface UseGlideOptions {
  modelPath?: string;
  config?: Partial<AppConfig>;
  enabled?: boolean;
}

export interface UseGlideReturn {
  videoRef: React.RefObject<HTMLVideoElement | null>;
  canvasRef: React.RefObject<HTMLCanvasElement | null>;
  isReady: boolean;
  isLoading: boolean;
  error: string | null;
  signals: TouchProofSignals;
  velocity: Vec2D | null;
  gestureState: GestureState;
  landmarks: Landmark[] | null;
  fps: number;
  config: AppConfig;
}

export function useGlide(options: UseGlideOptions = {}): UseGlideReturn {
  const { modelPath, config: configOverrides, enabled = true } = options;

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const frameCountRef = useRef(0);
  const lastFpsTimeRef = useRef(0);

  const [isReady, setIsReady] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [signals, setSignals] = useState<TouchProofSignals>(emptySignals());
  const [velocity, setVelocity] = useState<Vec2D | null>(null);
  const [gestureState, setGestureState] = useState<GestureState>(GestureState.IDLE);
  const [landmarks, setLandmarks] = useState<Landmark[] | null>(null);
  const [fps, setFps] = useState(0);

  const configRef = useRef<AppConfig>(
    configOverrides ? mergeConfig(configOverrides) : createDefaultConfig(),
  );

  // Pipeline objects stored in refs to avoid recreation
  const kinematicsRef = useRef<KinematicsTracker | null>(null);
  const touchproofRef = useRef<TouchProofDetector | null>(null);
  const velocityTrackerRef = useRef<VelocityTracker | null>(null);
  const velocityControllerRef = useRef<VelocityController | null>(null);

  // Throttle react state updates
  const updateCountRef = useRef(0);

  const initPipeline = useCallback(() => {
    const cfg = configRef.current;
    kinematicsRef.current = new KinematicsTracker(
      cfg.kinematics.emaAlpha,
      cfg.kinematics.bufferFrames,
    );
    touchproofRef.current = new TouchProofDetector(cfg.touchproof);
    velocityTrackerRef.current = new VelocityTracker();
    velocityControllerRef.current = new VelocityController();
  }, []);

  /** Run the pipeline on one video frame. Scheduling is owned by the effect. */
  const processFrame = useCallback((detector: WebHandDetector) => {
    const video = videoRef.current;

    if (!video || !detector.isReady || video.readyState < 2) return;

    const timestampMs = performance.now();
    const width = video.videoWidth;
    const height = video.videoHeight;

    // Detect hand
    const handDet = detector.detect(video, timestampMs);

    let currentSignals = emptySignals();
    let currentVelocity: Vec2D | null = null;
    let currentGestureState = GestureState.IDLE;
    let currentLandmarks: Landmark[] | null = null;

    if (handDet && handDet.landmarks.length >= 21) {
      currentLandmarks = handDet.landmarks;

      // Kinematics
      kinematicsRef.current?.compute(handDet.landmarks);

      // Poses
      const poses = checkHandPose(handDet.landmarks);

      // TouchProof detection
      if (touchproofRef.current) {
        currentSignals = touchproofRef.current.update(handDet.landmarks, width, height);
      }

      // Velocity tracking
      const indexTip = handDet.landmarks[8]!;
      const middleTip = handDet.landmarks[12]!;

      if (velocityTrackerRef.current) {
        currentVelocity = velocityTrackerRef.current.update(
          [indexTip.x, indexTip.y],
          [middleTip.x, middleTip.y],
          currentSignals.isTouching,
          timestampMs,
        );
      }

      // Velocity controller
      if (velocityControllerRef.current) {
        const velUpdate = velocityControllerRef.current.update(
          currentVelocity,
          currentSignals.isTouching,
          poses.openPalm && !currentSignals.isTouching,
          timestampMs,
        );
        currentGestureState = velUpdate.state;
        currentVelocity = velUpdate.velocity;
      }
    }

    // Throttle React state updates to every 2-3 frames
    updateCountRef.current++;
    if (updateCountRef.current % 2 === 0) {
      setSignals(currentSignals);
      setVelocity(currentVelocity);
      setGestureState(currentGestureState);
      setLandmarks(currentLandmarks);
    }

    // FPS calculation
    frameCountRef.current++;
    if (timestampMs - lastFpsTimeRef.current >= 1000) {
      setFps(frameCountRef.current);
      frameCountRef.current = 0;
      lastFpsTimeRef.current = timestampMs;
    }
  }, []);

  useEffect(() => {
    if (!enabled) return;

    // Everything below is owned by this run of the effect. Cleanup must not
    // read videoRef: React has already detached it by the time an unmount
    // cleanup runs, so the stream and element are tracked locally instead.
    let cancelled = false;
    let stream: MediaStream | null = null;
    let attachedVideo: HTMLVideoElement | null = null;
    let rafId: number | null = null;
    const detector = new WebHandDetector();

    const stopStream = (s: MediaStream | null) => {
      s?.getTracks().forEach((t) => t.stop());
    };

    const loop = () => {
      rafId = null;
      if (cancelled) return;
      processFrame(detector);
      if (!cancelled) rafId = requestAnimationFrame(loop);
    };

    const startPipeline = async () => {
      setIsLoading(true);
      setError(null);
      // Only getUserMedia failures get camera-specific messages; play() can
      // also reject with NotAllowedError (autoplay), which is not a permission issue.
      let requestingCamera = true;

      try {
        if (!cameraApiAvailable()) {
          setError(CAMERA_MESSAGES.unavailable);
          setIsLoading(false);
          return;
        }

        // Start camera
        const s = await navigator.mediaDevices.getUserMedia({
          video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' },
        });

        // Unmounted (or re-run under StrictMode) while the prompt was open.
        if (cancelled) {
          stopStream(s);
          return;
        }
        stream = s;
        requestingCamera = false;

        const video = videoRef.current;
        if (video) {
          attachedVideo = video;
          video.srcObject = s;
          await video.play();
        }
        if (cancelled) return;

        // Initialize MediaPipe
        await detector.initialize({ modelPath });

        if (cancelled) return;

        // Initialize pipeline objects
        initPipeline();

        setIsReady(true);
        setIsLoading(false);

        // Start processing loop
        rafId = requestAnimationFrame(loop);
      } catch (err) {
        if (cancelled) return;
        // The camera may have started before a later step failed.
        stopStream(stream);
        stream = null;
        if (attachedVideo) attachedVideo.srcObject = null;

        const message =
          (requestingCamera ? describeCameraError(err) : null) ??
          (err instanceof Error ? err.message : 'Failed to initialize Glide');
        setError(message);
        setIsLoading(false);
      }
    };

    startPipeline();

    return () => {
      cancelled = true;
      if (rafId !== null) cancelAnimationFrame(rafId);
      rafId = null;

      // Stop camera
      stopStream(stream);
      stream = null;
      if (attachedVideo) {
        attachedVideo.pause();
        attachedVideo.srcObject = null;
        attachedVideo = null;
      }

      detector.destroy();
      setIsReady(false);
    };
  }, [enabled, modelPath, initPipeline, processFrame]);

  return {
    videoRef,
    canvasRef,
    isReady,
    isLoading,
    error,
    signals,
    velocity,
    gestureState,
    landmarks,
    fps,
    config: configRef.current,
  };
}
