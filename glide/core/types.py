"""Core data types and configuration for Glide."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

# Import Pydantic configs from separate module


class GateState(Enum):
    UNARMED = "UNARMED"
    READY = "READY"
    ARMED = "ARMED"
    COOLDOWN = "COOLDOWN"


@dataclass
class Landmark:
    x: float
    y: float
    visibility: float | None = None  # MediaPipe visibility score
    presence: float | None = None  # MediaPipe presence score


@dataclass
class BBox:
    x: int
    y: int
    w: int
    h: int


@dataclass
class HandDet:
    landmarks: list[Landmark]
    handedness: str
    confidence: float
    bbox: BBox | None = None


@dataclass
class PoseFlags:
    open_palm: bool = False
    pointing_index: bool = False
    two_up: bool = False
