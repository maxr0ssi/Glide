"""Core data types and configuration for Glide."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional
import time

# Import Pydantic configs from separate module
from glide.core.config_models import (
    GatesConfig,
    KinematicsConfig,
    TwoFingerConfig,
    TouchProofConfig,
    CircularConfig,
    AppConfig,
)



class Mode(Enum):
    ONE_FINGER = "one_finger"
    TWO_FINGER = "two_finger"


class GateState(Enum):
    UNARMED = "UNARMED"
    READY = "READY"
    ARMED = "ARMED"
    COOLDOWN = "COOLDOWN"


@dataclass
class Landmark:
    x: float
    y: float
    visibility: Optional[float] = None  # MediaPipe visibility score
    presence: Optional[float] = None    # MediaPipe presence score


@dataclass
class BBox:
    x: int
    y: int
    w: int
    h: int


@dataclass
class HandDet:
    landmarks: List[Landmark]
    handedness: str
    confidence: float
    bbox: Optional[BBox] = None


@dataclass
class PoseFlags:
    open_palm: bool = False
    pointing_index: bool = False
    two_up: bool = False



# Note: Config classes are now imported from config_models.py above

# Legacy TwoFingerGateConfig (not in use)
@dataclass
class TwoFingerGateConfig:
    d_enter: float = 0.35  # Normalized distance to enter READY
    d_exit: float = 0.50   # Normalized distance to exit READY
    theta_enter_deg: float = 20.0  # Max angle between fingers to enter
    theta_exit_deg: float = 28.0   # Max angle to exit
    n_enter_frames: int = 3  # Frames needed to enter READY
    n_exit_frames: int = 3   # Frames needed to exit READY
    stillness_rms_max: float = 0.08  # Max RMS speed for stillness
    stillness_ms: int = 140  # Duration of stillness required
    corr_window_frames: int = 5  # Window for velocity correlation
    vel_corr_min: float = 0.70  # Min correlation to become ARMED


