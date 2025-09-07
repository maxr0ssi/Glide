"""Core data types and contracts for Glide."""

from glide.core.config_models import (
    AppConfig,
    # Pydantic config classes
    GatesConfig,
    KinematicsConfig,
    TouchProofConfig,
)
from glide.core.contracts import (
    FrameSource,
    GestureDetector,
    HandDetector,
)
from glide.core.types import (
    BBox,
    # Enums
    GateState,
    HandDet,
    # Data classes
    Landmark,
    PoseFlags,
)

__all__ = [
    # Contracts
    "FrameSource",
    "HandDetector",
    "GestureDetector",
    # Enums
    "GateState",
    # Data classes
    "Landmark",
    "BBox",
    "HandDet",
    "PoseFlags",
    # Config classes
    "GatesConfig",
    "KinematicsConfig",
    "TouchProofConfig",
    "AppConfig",
]
