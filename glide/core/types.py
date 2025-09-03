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
    TouchProofConfig,
    AppConfig,
)


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


