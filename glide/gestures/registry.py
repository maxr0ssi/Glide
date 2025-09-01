"""Lightweight plugin registry for gesture detectors.

This allows adding new gesture detectors without modifying core code.
"""

from typing import Dict, List, Any
from glide.core.contracts import GestureDetector


# Global registry of gesture detectors
_registry: Dict[str, GestureDetector] = {}


def register(name: str, detector: GestureDetector) -> None:
    """Register a gesture detector with a name.
    
    Args:
        name: Unique name for the detector (e.g., 'swish1', 'swish2')
        detector: Instance of a GestureDetector
    """
    _registry[name] = detector


def unregister(name: str) -> None:
    """Remove a gesture detector from the registry."""
    _registry.pop(name, None)


def list_all() -> List[str]:
    """List all registered gesture detector names."""
    return list(_registry.keys())


def get(name: str) -> GestureDetector:
    """Get a specific detector by name.
    
    Raises:
        KeyError: If detector not found
    """
    return _registry[name]


def get_active(priority_list: List[str]) -> List[GestureDetector]:
    """Get detectors in priority order.
    
    Args:
        priority_list: List of detector names in priority order
        
    Returns:
        List of detectors that exist in the registry
    """
    detectors = []
    for name in priority_list:
        if name in _registry:
            detectors.append(_registry[name])
    return detectors


def clear() -> None:
    """Clear all registered detectors (useful for testing)."""
    _registry.clear()