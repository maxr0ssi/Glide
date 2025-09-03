"""Scroll configuration."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ScrollConfig:
    """Configuration for scroll behavior."""
    # Mapping: 180 degrees ≈ 400 pixels
    pixels_per_degree: float = 2.22  # 400/180
    
    # Smooth scrolling parameters
    max_velocity: float = 100.0  # pixels per event
    acceleration_curve: float = 1.5  # exponential factor
    
    # Natural scrolling preference
    respect_system_preference: bool = True
    
    # HUD display
    show_hud: bool = True
    hud_fade_duration_ms: int = 500