"""Core data types and contracts for Glide."""

from glide.core.contracts import (
    FrameSource,
    HandDetector,
    GestureDetector,
    EventSink,
)
from glide.core.types import (
    # Enums
    Mode,
    GateState,
    # Data classes
    Landmark,
    BBox,
    HandDet,
    PoseFlags,
    # Legacy config
    TwoFingerGateConfig,
)
from glide.core.config_models import (
    # Pydantic config classes
    GatesConfig,
    KinematicsConfig,
    TwoFingerConfig,
    TouchProofConfig,
    CircularConfig,
    AppConfig,
)

__all__ = [
    # Contracts
    "FrameSource",
    "HandDetector",
    "GestureDetector",
    "EventSink",
    # Enums
    "Mode", 
    "GateState",
    # Data classes
    "Landmark",
    "BBox",
    "HandDet",
    "PoseFlags",
    # Config classes
    "GatesConfig",
    "KinematicsConfig",
    "TwoFingerConfig",
    "TwoFingerGateConfig",
    "TouchProofConfig",
    "CircularConfig",
    "AppConfig",
]