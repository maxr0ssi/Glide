from __future__ import annotations

from dataclasses import dataclass
from typing import Deque, List, Optional, Tuple
from collections import deque
import math

from glide.core.types import Landmark


@dataclass
class HandKinematics:
    palm_x: float
    palm_y: float
    theta_rad: float  # wrist -> middle MCP angle
    index_tip_rel: Tuple[float, float]
    middle_tip_rel: Optional[Tuple[float, float]]
    finger_length_idx: float
    finger_length_mid: Optional[float]


class KinematicsTracker:
    def __init__(self, ema_alpha: float = 0.35, buffer_frames: int = 24) -> None:
        self.ema_alpha = ema_alpha
        self.buffer_frames = buffer_frames
        self._idx_tip_ema: Optional[Tuple[float, float]] = None
        self._mid_tip_ema: Optional[Tuple[float, float]] = None
        self.trail: Deque[Tuple[float, float]] = deque(maxlen=buffer_frames)
        self.trail_mid: Deque[Tuple[float, float]] = deque(maxlen=buffer_frames)  # Middle finger trail
        self.trail_mean: Deque[Tuple[float, float]] = deque(maxlen=buffer_frames)  # Mean of both fingers

    @staticmethod
    def _mean(points: List[Tuple[float, float]]) -> Tuple[float, float]:
        sx = sum(p[0] for p in points)
        sy = sum(p[1] for p in points)
        n = max(len(points), 1)
        return sx / n, sy / n

    @staticmethod
    def _rot(px: float, py: float, theta: float) -> Tuple[float, float]:
        c, s = math.cos(theta), math.sin(theta)
        return c * px - s * py, s * px + c * py

    def compute(self, landmarks: List[Landmark]) -> Optional[HandKinematics]:
        if not landmarks or len(landmarks) < 21:
            return None
        wrist = landmarks[0]
        # MCPs: index=5, middle=9, ring=13, pinky=17
        mcps = [landmarks[i] for i in (5, 9, 13, 17)]
        palm_x, palm_y = self._mean([(p.x, p.y) for p in [wrist] + mcps])

        mid_mcp = landmarks[9]
        theta = math.atan2(mid_mcp.y - wrist.y, mid_mcp.x - wrist.x)

        idx_tip = landmarks[8]
        mid_tip = landmarks[12]
        idx_mcp = landmarks[5]
        mid_mcp_lmk = landmarks[9]

        # Hand-aligned, palm-relative coordinates
        idx_rel = (idx_tip.x - palm_x, idx_tip.y - palm_y)
        mid_rel = (mid_tip.x - palm_x, mid_tip.y - palm_y)
        idx_rel_aligned = self._rot(idx_rel[0], idx_rel[1], -theta)
        mid_rel_aligned = self._rot(mid_rel[0], mid_rel[1], -theta)

        # EMA smoothing of tips in aligned space
        self._idx_tip_ema = self._ema(self._idx_tip_ema, idx_rel_aligned, self.ema_alpha)
        self._mid_tip_ema = self._ema(self._mid_tip_ema, mid_rel_aligned, self.ema_alpha)

        # Finger lengths as normalization scale
        finger_len_idx = math.hypot(idx_tip.x - idx_mcp.x, idx_tip.y - idx_mcp.y)
        finger_len_mid = math.hypot(mid_tip.x - mid_mcp_lmk.x, mid_tip.y - mid_mcp_lmk.y)

        # Update trails (aligned coords)
        self.trail.append(self._idx_tip_ema)
        self.trail_mid.append(self._mid_tip_ema)
        
        # Update mean trail
        mean_x = (self._idx_tip_ema[0] + self._mid_tip_ema[0]) / 2.0
        mean_y = (self._idx_tip_ema[1] + self._mid_tip_ema[1]) / 2.0
        self.trail_mean.append((mean_x, mean_y))

        return HandKinematics(
            palm_x=palm_x,
            palm_y=palm_y,
            theta_rad=theta,
            index_tip_rel=self._idx_tip_ema,
            middle_tip_rel=self._mid_tip_ema,
            finger_length_idx=finger_len_idx,
            finger_length_mid=finger_len_mid,
        )

    @staticmethod
    def _ema(prev: Optional[Tuple[float, float]], cur: Tuple[float, float], alpha: float) -> Tuple[float, float]:
        if prev is None:
            return cur
        return (alpha * cur[0] + (1 - alpha) * prev[0], alpha * cur[1] + (1 - alpha) * prev[1])
    
    def get_mean_fingertip(self) -> Optional[Tuple[float, float]]:
        """Get the mean position of index and middle fingertips."""
        if self._idx_tip_ema is None or self._mid_tip_ema is None:
            return None
        return (
            (self._idx_tip_ema[0] + self._mid_tip_ema[0]) / 2.0,
            (self._idx_tip_ema[1] + self._mid_tip_ema[1]) / 2.0
        )
    
    def get_finger_speeds(self, lookback: int = 1) -> Tuple[Optional[float], Optional[float]]:
        """Get normalized speeds of index and middle fingers."""
        idx_speed = None
        mid_speed = None
        
        if len(self.trail) > lookback:
            dx = self.trail[-1][0] - self.trail[-(lookback+1)][0]
            dy = self.trail[-1][1] - self.trail[-(lookback+1)][1]
            idx_speed = math.hypot(dx, dy)
        
        if len(self.trail_mid) > lookback:
            dx = self.trail_mid[-1][0] - self.trail_mid[-(lookback+1)][0]
            dy = self.trail_mid[-1][1] - self.trail_mid[-(lookback+1)][1]
            mid_speed = math.hypot(dx, dy)
        
        return idx_speed, mid_speed


