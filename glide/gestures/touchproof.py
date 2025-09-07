from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import math

import cv2
import numpy as np

from glide.core.types import GateState, Landmark
from glide.core.config_models import TouchProofConfig
from glide.features.alignment import HandAligner


@dataclass
class TouchProofSignals:
    """All signals used for touch detection."""

    proximity_score: float  # 0-1 (closer = higher)
    angle_score: float  # 0-1 (more parallel = higher)
    correlation_score: float  # 0-1 (moving together = higher)
    visibility_score: float  # 0-1 (asymmetry = higher)
    mfc_score: float  # 0-1 (coherent motion = higher)
    distance_factor: float  # 0-1 (0=close, 1=far)
    fused_score: float  # 0-1 (overall confidence)
    is_touching: bool  # Final decision


class MicroFlowTracker:
    """Track optical flow coherence between fingertips."""

    def __init__(self, window_frames: int = 5, patch_size: int = 15):
        self.window_frames = window_frames
        self.patch_size = patch_size
        self.prev_gray: np.ndarray | None = None
        self.flow_history: deque[tuple[np.ndarray, np.ndarray]] = deque(maxlen=window_frames)

        # Lucas-Kanade parameters
        self.lk_params = dict(
            winSize=(15, 15),
            maxLevel=2,
            criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03),
        )

    def update(
        self, frame_gray: np.ndarray, tip_a: tuple[float, float], tip_b: tuple[float, float]
    ) -> float:
        """
        Update flow tracking and compute coherence score.

        Returns:
            mfc_score: 0-1 where 1 = perfectly coherent motion
        """
        if self.prev_gray is None:
            self.prev_gray = frame_gray.copy()
            return 0.5  # No history yet

        # Convert to numpy arrays
        pts_prev = np.array([[tip_a], [tip_b]], dtype=np.float32)

        # Calculate optical flow
        pts_next, status, error = cv2.calcOpticalFlowPyrLK(
            self.prev_gray, frame_gray, pts_prev, None, **self.lk_params
        )

        # Check if flow was successfully computed
        if status[0] == 0 or status[1] == 0:
            self.prev_gray = frame_gray.copy()
            return 0.5  # Flow failed, uncertain

        # Compute flow vectors
        flow_a = pts_next[0] - pts_prev[0]
        flow_b = pts_next[1] - pts_prev[1]

        # Store in history
        self.flow_history.append((flow_a[0], flow_b[0]))

        # Update previous frame
        self.prev_gray = frame_gray.copy()

        # Need enough history
        if len(self.flow_history) < 3:
            return 0.5

        # Compute correlation and magnitude ratio over history
        flows_a = np.array([f[0] for f in self.flow_history])
        flows_b = np.array([f[1] for f in self.flow_history])

        # Dominant axis correlation
        corr_x = np.corrcoef(flows_a[:, 0], flows_b[:, 0])[0, 1]
        corr_y = np.corrcoef(flows_a[:, 1], flows_b[:, 1])[0, 1]

        # Handle NaN from zero variance conservatively (avoid false positives)
        if np.isnan(corr_x):
            corr_x = 0.0
        if np.isnan(corr_y):
            corr_y = 0.0

        # Average correlation
        avg_corr = (corr_x + corr_y) / 2.0

        # Magnitude ratio
        mag_a = np.linalg.norm(flows_a, axis=1).mean()
        mag_b = np.linalg.norm(flows_b, axis=1).mean()

        if mag_a < 1e-6 and mag_b < 1e-6:
            # Both stationary: return neutral/low confidence to avoid inflating fused score
            return 0.0
        if mag_a < 1e-6 or mag_b < 1e-6:
            # One stationary
            mag_ratio_score = 0.0
        else:
            # Compute ratio
            mag_ratio = min(mag_a, mag_b) / max(mag_a, mag_b)
            mag_ratio_score = 1.0 if 0.6 <= mag_ratio <= 1.0 else 0.0

        # Combine correlation and magnitude agreement
        mfc_score = 0.7 * max(0, avg_corr) + 0.3 * mag_ratio_score

        return float(np.clip(mfc_score, 0, 1))


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

        proximity_score_raw = self._score_proximity(proximity_norm)

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

        angle_score = self._score_angle(self._angle_ema)

        # 3. MOTION CORRELATION SIGNAL
        # Update position buffers
        idx_aligned = self.aligner.to_hand_aligned(index_tip.x, index_tip.y)
        mid_aligned = self.aligner.to_hand_aligned(middle_tip.x, middle_tip.y)
        self._idx_positions.append(idx_aligned)
        self._mid_positions.append(mid_aligned)

        correlation_score = self._compute_correlation()

        # 4. VISIBILITY/OCCLUSION SIGNAL
        visibility_score = self._score_visibility(index_tip, middle_tip)

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
        weights = self._get_adaptive_weights(distance_factor)

        # Adjust proximity/angle thresholds based on distance
        proximity_adj = self._adjust_proximity_threshold(proximity_norm, distance_factor)
        angle_adj = self._adjust_angle_threshold(angle_deg, distance_factor)

        # Recalculate scores with adjusted thresholds
        proximity_score_adj = self._score_proximity_adjusted(proximity_norm, distance_factor)
        angle_score_adj = self._score_angle_adjusted(angle_deg, distance_factor)

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

    def _score_proximity(self, distance_norm: float) -> float:
        """Convert normalized distance to proximity score (0-1)."""
        # Closer = higher score
        # Use smooth transition between enter and exit thresholds
        if distance_norm <= self.config.proximity_enter:
            return 1.0
        if distance_norm >= self.config.proximity_exit:
            return 0.0
        # Linear interpolation
        range_size = self.config.proximity_exit - self.config.proximity_enter
        return float(1.0 - (distance_norm - self.config.proximity_enter) / range_size)

    def _score_angle(self, angle_deg: float) -> float:
        """Convert angle to score (0-1)."""
        # More parallel = higher score
        if angle_deg <= self.config.angle_enter_deg:
            return 1.0
        if angle_deg >= self.config.angle_exit_deg:
            return 0.0
        range_size = self.config.angle_exit_deg - self.config.angle_enter_deg
        return float(1.0 - (angle_deg - self.config.angle_enter_deg) / range_size)

    def _compute_correlation(self) -> float:
        """Compute velocity correlation between fingers."""
        if len(self._idx_positions) < self.config.correlation_frames:
            return 0.5  # Neutral until we have enough data

        # Compute velocities
        idx_vels = []
        mid_vels = []

        for i in range(1, len(self._idx_positions)):
            # Index finger velocity
            dx_idx = self._idx_positions[i][0] - self._idx_positions[i - 1][0]
            dy_idx = self._idx_positions[i][1] - self._idx_positions[i - 1][1]
            idx_vels.append((dx_idx, dy_idx))

            # Middle finger velocity
            dx_mid = self._mid_positions[i][0] - self._mid_positions[i - 1][0]
            dy_mid = self._mid_positions[i][1] - self._mid_positions[i - 1][1]
            mid_vels.append((dx_mid, dy_mid))

        # Compute correlation for x and y separately
        idx_vx = [v[0] for v in idx_vels]
        idx_vy = [v[1] for v in idx_vels]
        mid_vx = [v[0] for v in mid_vels]
        mid_vy = [v[1] for v in mid_vels]

        corr_x = self._pearson_correlation(idx_vx, mid_vx)
        corr_y = self._pearson_correlation(idx_vy, mid_vy)

        # Average correlation
        if corr_x is not None and corr_y is not None:
            avg_corr = (corr_x + corr_y) / 2.0
        elif corr_x is not None:
            avg_corr = corr_x
        elif corr_y is not None:
            avg_corr = corr_y
        else:
            avg_corr = 0.5

        # Convert to 0-1 score
        if avg_corr >= self.config.correlation_min:
            return 1.0
        return max(0.0, avg_corr)

    def _score_visibility(self, index_tip: Landmark, middle_tip: Landmark) -> float:
        """Score based on visibility asymmetry (occlusion indicator)."""
        if index_tip.visibility is None or middle_tip.visibility is None:
            return 0.5  # Neutral if no visibility data

        # When fingers overlap, one typically has lower visibility
        asymmetry = abs(index_tip.visibility - middle_tip.visibility)

        if asymmetry >= self.config.visibility_asymmetry_min:
            return 1.0
        return float(asymmetry / self.config.visibility_asymmetry_min)

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

    def _pearson_correlation(self, a: list[float], b: list[float]) -> float | None:
        """Calculate Pearson correlation coefficient."""
        n = min(len(a), len(b))
        if n < 2:
            return None

        mean_a = sum(a) / n
        mean_b = sum(b) / n

        # Handle constant series
        var_a = sum((x - mean_a) ** 2 for x in a)
        var_b = sum((x - mean_b) ** 2 for x in b)

        if var_a < 1e-9 or var_b < 1e-9:
            return 1.0 if var_a < 1e-9 and var_b < 1e-9 else 0.0

        cov = sum((a[i] - mean_a) * (b[i] - mean_b) for i in range(n))
        return cov / math.sqrt(var_a * var_b)

    def _get_adaptive_weights(self, distance_factor: float) -> dict[str, float]:
        """Get fusion weights based on hand distance."""
        if distance_factor > 0.7:  # Far away
            return {"proximity": 0.45, "angle": 0.20, "mfc": 0.30, "occlusion": 0.05}
        if distance_factor < 0.3:  # Very close - reduced angle weight for laptop cameras
            return {"proximity": 0.40, "angle": 0.30, "mfc": 0.25, "occlusion": 0.05}
        # Interpolate
        # Linear interpolation between near and far weights
        t = (distance_factor - 0.3) / 0.4  # Map [0.3, 0.7] to [0, 1]
        near_weights = {"proximity": 0.40, "angle": 0.30, "mfc": 0.25, "occlusion": 0.05}
        far_weights = {"proximity": 0.45, "angle": 0.20, "mfc": 0.30, "occlusion": 0.05}
        return {k: near_weights[k] * (1 - t) + far_weights[k] * t for k in near_weights}

    def _adjust_proximity_threshold(self, proximity_norm: float, distance_factor: float) -> float:
        """Adjust proximity threshold based on distance."""
        # Not used directly, but kept for reference
        return proximity_norm

    def _adjust_angle_threshold(self, angle_deg: float, distance_factor: float) -> float:
        """Adjust angle threshold based on distance."""
        # Not used directly, but kept for reference
        return angle_deg

    def _score_proximity_adjusted(self, distance_norm: float, distance_factor: float) -> float:
        """Score proximity with distance-aware thresholds and relative baseline."""
        # Mode-based scoring
        if self.config.proximity_mode == "adaptive":
            # Try relative scoring if baselines are available
            baseline = self._get_baseline_distance(distance_factor)
            if baseline is not None:
                # Relative proximity: how much closer than usual?
                relative_proximity = baseline / (distance_norm + 0.001)  # Avoid division by zero

                # Sigmoid scoring centered at threshold
                center = self.config.relative_touch_threshold
                steepness = 6.0
                score = 1.0 / (1.0 + np.exp(-steepness * (relative_proximity - center)))
                return float(score)

        # Fallback to threshold-based scoring with distance adjustment
        k_d = getattr(self.config, "k_d", 0.3)  # Use config value
        # Stricter when far (distance_factor=1), looser when close (0)
        enter_adjusted = self.config.proximity_enter * (1 + k_d * distance_factor)
        exit_adjusted = self.config.proximity_exit * (1 + k_d * distance_factor)

        # Score with adjusted thresholds
        if distance_norm <= enter_adjusted:
            return 1.0
        if distance_norm >= exit_adjusted:
            return 0.0
        range_size = exit_adjusted - enter_adjusted
        return float(1.0 - (distance_norm - enter_adjusted) / range_size)

    def _score_angle_adjusted(self, angle_deg: float, distance_factor: float) -> float:
        """Score angle with distance-aware thresholds."""
        # Adjust thresholds: stricter (smaller) when close
        k_theta = getattr(self.config, "k_theta", 4.0)  # Angle interaction coefficient
        enter_adjusted = self.config.angle_enter_deg - k_theta * (1 - distance_factor)
        exit_adjusted = self.config.angle_exit_deg - k_theta * (1 - distance_factor)

        # Score with adjusted thresholds
        if angle_deg <= enter_adjusted:
            return 1.0
        if angle_deg >= exit_adjusted:
            return 0.0
        range_size = exit_adjusted - enter_adjusted
        return float(1.0 - (angle_deg - enter_adjusted) / range_size)

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
