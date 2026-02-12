/**
 * Visualizer — webcam canvas with hand landmarks, signal dashboard, and FPS counter.
 */

import React, { useEffect } from 'react';
import type { Landmark } from '../core/types';
import type { TouchProofSignals } from '../gestures/touchproof-signals';
import { GestureState } from '../gestures/velocity-controller';

// MediaPipe hand connections (pairs of landmark indices)
const HAND_CONNECTIONS: [number, number][] = [
  [0, 1], [1, 2], [2, 3], [3, 4],       // thumb
  [0, 5], [5, 6], [6, 7], [7, 8],       // index
  [5, 9], [9, 10], [10, 11], [11, 12],  // middle
  [9, 13], [13, 14], [14, 15], [15, 16], // ring
  [13, 17], [17, 18], [18, 19], [19, 20], // pinky
  [0, 17],                                // palm
];

interface VisualizerProps {
  videoRef: React.RefObject<HTMLVideoElement | null>;
  canvasRef: React.RefObject<HTMLCanvasElement | null>;
  landmarks: Landmark[] | null;
  signals: TouchProofSignals;
  gestureState: GestureState;
  fps: number;
  isLoading: boolean;
  error: string | null;
}

export const Visualizer: React.FC<VisualizerProps> = ({
  videoRef,
  canvasRef,
  landmarks,
  signals,
  gestureState,
  fps,
  isLoading,
  error,
}) => {
  // Draw landmarks overlay
  useEffect(() => {
    const canvas = canvasRef.current;
    const video = videoRef.current;
    if (!canvas || !video) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const draw = () => {
      canvas.width = video.videoWidth || 640;
      canvas.height = video.videoHeight || 480;

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      if (!landmarks || landmarks.length < 21) return;

      const w = canvas.width;
      const h = canvas.height;

      // Draw connections
      ctx.lineWidth = 2;
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.6)';
      for (const [a, b] of HAND_CONNECTIONS) {
        const la = landmarks[a]!;
        const lb = landmarks[b]!;
        ctx.beginPath();
        ctx.moveTo(la.x * w, la.y * h);
        ctx.lineTo(lb.x * w, lb.y * h);
        ctx.stroke();
      }

      // Draw landmarks
      for (let i = 0; i < landmarks.length; i++) {
        const lm = landmarks[i]!;
        const isFingerTip = i === 8 || i === 12;

        ctx.beginPath();
        ctx.arc(lm.x * w, lm.y * h, isFingerTip ? 6 : 3, 0, Math.PI * 2);

        if (isFingerTip) {
          ctx.fillStyle = signals.isTouching ? '#22c55e' : '#ef4444';
        } else {
          ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
        }
        ctx.fill();
      }
    };

    const interval = setInterval(draw, 50);
    return () => clearInterval(interval);
  }, [canvasRef, videoRef, landmarks, signals.isTouching]);

  const signalBars = [
    { label: 'Proximity', value: signals.proximityScore, color: '#3b82f6' },
    { label: 'Angle', value: signals.angleScore, color: '#8b5cf6' },
    { label: 'Correlation', value: signals.correlationScore, color: '#06b6d4' },
    { label: 'Visibility', value: signals.visibilityScore, color: '#f59e0b' },
    { label: 'Fused', value: signals.fusedScore, color: signals.isTouching ? '#22c55e' : '#ef4444' },
  ];

  return (
    <div className="glide-visualizer">
      <div className="glide-video-container">
        <video
          ref={videoRef as React.RefObject<HTMLVideoElement>}
          autoPlay
          playsInline
          muted
          style={{ width: '100%', height: '100%', objectFit: 'cover', transform: 'scaleX(-1)' }}
        />
        <canvas
          ref={canvasRef as React.RefObject<HTMLCanvasElement>}
          className="glide-canvas-overlay"
          style={{ transform: 'scaleX(-1)' }}
        />

        {/* Status overlay */}
        <div className="glide-status-overlay">
          <span className="glide-fps">{fps} FPS</span>
          <span className={`glide-state glide-state--${gestureState}`}>
            {gestureState === GestureState.SCROLLING ? 'SCROLLING' : 'IDLE'}
          </span>
        </div>

        {/* Loading overlay */}
        {isLoading && (
          <div className="glide-loading-overlay">
            <div className="glide-spinner" />
            <p>Loading hand detection model...</p>
          </div>
        )}

        {/* Error overlay */}
        {error && (
          <div className="glide-error-overlay">
            <p>{error}</p>
          </div>
        )}
      </div>

      {/* Signal dashboard */}
      <div className="glide-signal-dashboard">
        {signalBars.map((bar) => (
          <div key={bar.label} className="glide-signal-row">
            <span className="glide-signal-label">{bar.label}</span>
            <div className="glide-signal-bar-bg">
              <div
                className="glide-signal-bar-fill"
                style={{
                  width: `${Math.max(0, Math.min(100, bar.value * 100))}%`,
                  backgroundColor: bar.color,
                }}
              />
            </div>
            <span className="glide-signal-value">{bar.value.toFixed(2)}</span>
          </div>
        ))}
        <div className="glide-signal-row">
          <span className="glide-signal-label">Distance</span>
          <div className="glide-signal-bar-bg">
            <div
              className="glide-signal-bar-fill"
              style={{
                width: `${signals.distanceFactor * 100}%`,
                backgroundColor: '#64748b',
              }}
            />
          </div>
          <span className="glide-signal-value">{signals.distanceFactor.toFixed(2)}</span>
        </div>
      </div>
    </div>
  );
};
