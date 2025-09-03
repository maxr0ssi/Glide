"""Core contracts (interfaces) for Glide components.

These simple ABCs define boundaries between modules without overengineering.
"""

from abc import ABC, abstractmethod
from typing import Optional, Any, Dict
import numpy as np


class Frame:
    """Simple frame container."""
    def __init__(self, image: np.ndarray, timestamp_ms: int, metadata: Optional[Dict[str, Any]] = None):
        self.image = image
        self.timestamp_ms = timestamp_ms
        self.metadata = metadata or {}
        self.height, self.width = image.shape[:2]


class FrameSource(ABC):
    """Source of frames (camera, video file, replay)."""
    
    @abstractmethod
    def read(self) -> Optional[Frame]:
        """Read next frame. Returns None if no more frames."""
        pass
    
    @abstractmethod
    def release(self) -> None:
        """Clean up resources."""
        pass


class HandDetector(ABC):
    """Detects hands in images."""
    
    @abstractmethod
    def detect(self, image: np.ndarray) -> Optional[Any]:
        """Detect hands in image. Returns HandDet or None."""
        pass


class GestureDetector(ABC):
    """Detects gestures from hand/motion data."""
    
    @abstractmethod
    def update(self, state: Any) -> Optional[Any]:
        """Update with new state. Returns detected event or None."""
        pass
    
    @abstractmethod
    def reset(self) -> None:
        """Reset detector state."""
        pass


