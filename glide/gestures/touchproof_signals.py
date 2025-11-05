"""TouchProof signals and optical flow tracking."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import cv2
import numpy as np


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
