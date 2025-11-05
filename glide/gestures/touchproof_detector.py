"""Main TouchProof detector with state management."""

from __future__ import annotations

from collections import deque

import cv2
import numpy as np

from glide.core.config_models import TouchProofConfig
from glide.core.types import GateState, Landmark
from glide.features.alignment import HandAligner
from glide.gestures.touchproof_scoring import (
    compute_correlation,
    get_adaptive_weights,
    score_angle,
    score_angle_adjusted,
    score_proximity,
    score_proximity_adjusted,
    score_visibility,
)
from glide.gestures.touchproof_signals import MicroFlowTracker, TouchProofSignals


class TouchProofDetector:
    """Multi-signal fusion for robust fingertip contact detection."""

    def __init__(self, config: TouchProofConfig):
        self.config = config
        self.aligner = HandAligner()

        # State tracking
        self.state = GateState.UNARMED
        self._enter_counter = 0
        self._exit_counter = 0

        # Velocity tracking for correlation
        self._idx_positions: deque[tuple[float, float]] = deque(
            maxlen=config.correlation_frames + 1
        )
        self._mid_positions: deque[tuple[float, float]] = deque(
            maxlen=config.correlation_frames + 1
        )

        # Previous frame for velocity
        self._last_update_ms = 0

        # EMA smoothing for volatile signals
        self._proximity_ema: float | None = None
        self._angle_ema: float | None = None  # Added angle smoothing for laptop cameras

        # Baseline tracking for adaptive proximity
        self._baseline_close: float | None = None  # Typical distance when close
        self._baseline_far: float | None = None  # Typical distance when far
        self._baseline_alpha = config.baseline_learning_rate  # From config

        # Micro-flow tracker
        self.flow_tracker = MicroFlowTracker(
            window_frames=config.mfc_window_frames, patch_size=config.mfc_patch_size
        )

        # Cache for expensive computations
        self._last_mfc_score = 0.5

    def update(
        self, landmarks: list[Landmark], frame_bgr: np.ndarray, image_width: int, image_height: int
    ) -> TouchProofSignals:
        """
        Update touch detection with new frame data.

        Args:
            landmarks: Hand landmarks from MediaPipe
            frame_bgr: Current camera frame
            image_width: Frame width
            image_height: Frame height

        Returns:
            TouchProofSignals with all detection signals and final decision
        """
        # Update hand alignment
        if not self.aligner.update(landmarks, image_width, image_height):
            return self._empty_signals()

        # Get fingertip info
        if len(landmarks) < 21:
            return self._empty_signals()

        index_tip = landmarks[8]
        middle_tip = landmarks[12]

        # 1. PROXIMITY SIGNAL
        if self.config.proximity_mode == "logarithmic":
            proximity_norm = self.aligner.get_normalized_distance_log(landmarks)
        else:
            proximity_norm = self.aligner.get_normalized_distance(landmarks)

        # HARD CAP: If fingers are too far apart, no need to compute anything else
        if proximity_norm > self.config.proximity_hard_cap:
            return TouchProofSignals(
                proximity_score=0.0,
                angle_score=0.0,
                correlation_score=0.0,
                visibility_score=0.0,
                mfc_score=0.0,
                distance_factor=self.aligner.get_hand_distance_factor(),
                fused_score=0.0,
                is_touching=False,
            )

        proximity_score_raw = score_proximity(
            proximity_norm, self.config.proximity_enter, self.config.proximity_exit
        )

        # Apply EMA smoothing if enabled
        if self.config.smooth_proximity:
            if self._proximity_ema is None:
                self._proximity_ema = proximity_score_raw
            else:
                self._proximity_ema = (
                    self.config.ema_alpha * proximity_score_raw
                    + (1 - self.config.ema_alpha) * self._proximity_ema
                )
            proximity_score = self._proximity_ema
        else:
            proximity_score = proximity_score_raw

        # 2. ANGLE SIGNAL
        angle_deg = self.aligner.get_fingertip_angle(landmarks)

        # HARD CAP: If fingers are pointing in very different directions
        if angle_deg > self.config.angle_hard_cap_deg:
            return TouchProofSignals(
                proximity_score=proximity_score,
                angle_score=0.0,
                correlation_score=0.0,
                visibility_score=0.0,
                mfc_score=0.0,
                distance_factor=self.aligner.get_hand_distance_factor(),
                fused_score=0.0,
                is_touching=False,
            )

        # Apply angle smoothing for laptop camera stability
        angle_alpha = 0.2  # Faster response than proximity (0.3)
        if self._angle_ema is None:
            self._angle_ema = angle_deg
        else:
            self._angle_ema = angle_alpha * angle_deg + (1 - angle_alpha) * self._angle_ema

        angle_score = score_angle(
            self._angle_ema, self.config.angle_enter_deg, self.config.angle_exit_deg
        )

        # 3. MOTION CORRELATION SIGNAL
        # Update position buffers
        idx_aligned = self.aligner.to_hand_aligned(index_tip.x, index_tip.y)
        mid_aligned = self.aligner.to_hand_aligned(middle_tip.x, middle_tip.y)
        self._idx_positions.append(idx_aligned)
        self._mid_positions.append(mid_aligned)

        correlation_score = compute_correlation(
            self._idx_positions,
            self._mid_positions,
            self.config.correlation_frames,
            self.config.correlation_min,
        )

        # 4. VISIBILITY/OCCLUSION SIGNAL
        visibility_score = score_visibility(
            index_tip, middle_tip, self.config.visibility_asymmetry_min
        )

        # 5. Get fingertip pixel coordinates (needed for MFC)
        index_px, middle_px = self.aligner.get_fingertip_pixels(landmarks)

        # 6. Get distance factor for adaptive fusion
        distance_factor = self.aligner.get_hand_distance_factor()

        # 6b. Update baseline distances for adaptive proximity
        self._update_baseline(proximity_norm, distance_factor)

        # 7. Compute initial fused score for conditional logic
        initial_fused = 0.7 * proximity_score + 0.3 * angle_score

        # 8. MFC (Micro-Flow Cohesion) - expanded band for laptop cameras
        if (
            self.state == GateState.READY
            or (0.40 <= initial_fused <= 0.70)  # Expanded uncertainty band
            or distance_factor < 0.3
        ):  # Always compute when very close
            # Convert to grayscale for optical flow
            gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
            mfc_score = self.flow_tracker.update(gray, index_px, middle_px)
            self._last_mfc_score = mfc_score
        else:
            mfc_score = self._last_mfc_score

        # 9. DISTANCE-AWARE FUSION
        weights = get_adaptive_weights(distance_factor)

        # Get baseline for adaptive mode
        baseline = self._get_baseline_distance(distance_factor)

        # Recalculate scores with adjusted thresholds
        proximity_score_adj = score_proximity_adjusted(
            proximity_norm, distance_factor, self.config, baseline
        )
        angle_score_adj = score_angle_adjusted(angle_deg, distance_factor, self.config)

        # Fuse all signals with adaptive weights
        fused_score = (
            weights["proximity"] * proximity_score_adj
            + weights["angle"] * angle_score_adj
            + weights["mfc"] * mfc_score
            + weights["occlusion"] * visibility_score
        )

        # STATE MACHINE with hysteresis
        is_touching = self._update_state(fused_score)

        return TouchProofSignals(
            proximity_score=proximity_score_adj,
            angle_score=angle_score_adj,
            correlation_score=correlation_score,
            visibility_score=visibility_score,
            mfc_score=mfc_score,
            distance_factor=distance_factor,
            fused_score=fused_score,
            is_touching=is_touching,
        )

    def _update_state(self, fused_score: float) -> bool:
        """Update state machine with hysteresis."""
        # Simple threshold with hysteresis
        if self.state == GateState.UNARMED:
            if fused_score > self.config.fused_enter_threshold:
                self._enter_counter += 1
                if self._enter_counter >= self.config.frames_to_enter:
                    self.state = GateState.READY
                    self._enter_counter = 0
                    return True
            else:
                self._enter_counter = 0
            return False

        if self.state == GateState.READY:
            if fused_score < self.config.fused_exit_threshold:
                self._exit_counter += 1
                if self._exit_counter >= self.config.frames_to_exit:
                    self.state = GateState.UNARMED
                    self._exit_counter = 0
                    return False
            else:
                self._exit_counter = 0
            return True

        return False

    def _empty_signals(self) -> TouchProofSignals:
        """Return empty signals when detection fails."""
        return TouchProofSignals(
            proximity_score=0.0,
            angle_score=0.0,
            correlation_score=0.0,
            visibility_score=0.0,
            mfc_score=0.0,
            distance_factor=0.5,
            fused_score=0.0,
            is_touching=False,
        )

    def _update_baseline(self, distance_norm: float, distance_factor: float) -> None:
        """Update baseline distances for different hand distances."""
        # Only update when not touching (to learn normal separation)
        if self.state == GateState.UNARMED:
            if distance_factor < 0.3:  # Close
                if self._baseline_close is None:
                    self._baseline_close = distance_norm
                else:
                    self._baseline_close = (
                        self._baseline_alpha * distance_norm
                        + (1 - self._baseline_alpha) * self._baseline_close
                    )
            elif distance_factor > 0.7:  # Far
                if self._baseline_far is None:
                    self._baseline_far = distance_norm
                else:
                    self._baseline_far = (
                        self._baseline_alpha * distance_norm
                        + (1 - self._baseline_alpha) * self._baseline_far
                    )

    def _get_baseline_distance(self, distance_factor: float) -> float | None:
        """Get expected baseline distance for current hand distance."""
        if self._baseline_close is None or self._baseline_far is None:
            return None

        if distance_factor < 0.3:
            return self._baseline_close
        if distance_factor > 0.7:
            return self._baseline_far
        # Linear interpolation
        t = (distance_factor - 0.3) / 0.4
        return self._baseline_close * (1 - t) + self._baseline_far * t
