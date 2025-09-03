"""Core data types and contracts for Glide."""

from glide.core.contracts import (
    FrameSource,
    HandDetector,
    GestureDetector,
)
from glide.core.types import (
    # Enums
    GateState,
    # Data classes
    Landmark,
    BBox,
    HandDet,
    PoseFlags,
)
from glide.core.config_models import (
    # Pydantic config classes
    GatesConfig,
    KinematicsConfig,
    TouchProofConfig,
    AppConfig,
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