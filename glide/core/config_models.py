"""Pydantic models for configuration validation."""

from typing import List, Tuple, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator
import yaml


class GatesConfig(BaseModel):
    """Configuration for hand detection gates."""
    presence_conf: float = Field(0.7, ge=0.0, le=1.0, description="Minimum confidence for hand presence")
    poses: List[str] = Field(
        default=["open_palm", "pointing_index", "two_up"],
        description="List of required poses"
    )
    pre_still_ms: int = Field(150, ge=0, description="Pre-stillness duration in milliseconds")
    max_idle_rms_speed: float = Field(0.08, ge=0.0, description="Maximum RMS speed for idle detection")
    
    @field_validator('poses')
    @classmethod
    def validate_poses(cls, v: List[str]) -> List[str]:
        valid_poses = {"open_palm", "pointing_index", "two_up"}
        for pose in v:
            if pose not in valid_poses:
                raise ValueError(f"Invalid pose: {pose}. Must be one of {valid_poses}")
        return v


class KinematicsConfig(BaseModel):
    """Configuration for kinematics tracking."""
    ema_alpha: float = Field(0.35, ge=0.0, le=1.0, description="Exponential moving average alpha")
    buffer_frames: int = Field(24, ge=1, le=100, description="Number of frames to buffer")
    frame_lookback: int = Field(5, ge=1, le=10, description="Frames to look back for detection")



class ScrollConfig(BaseModel):
    """Configuration for scroll behavior."""
    enabled: bool = Field(True, description="Enable scroll functionality")
    pixels_per_degree: float = Field(2.22, ge=0.1, le=10.0, description="Pixels per degree of rotation")
    max_velocity: float = Field(100.0, ge=10.0, le=500.0, description="Maximum scroll velocity (pixels/event)")
    acceleration_curve: float = Field(1.5, ge=1.0, le=3.0, description="Acceleration curve exponent")
    respect_system_preference: bool = Field(True, description="Respect natural scrolling preference")
    show_hud: bool = Field(True, description="Show HUD overlay")
    hud_fade_duration_ms: int = Field(500, ge=100, le=2000, description="HUD fade duration (ms)")
    hud_position: str = Field("bottom-right", description="HUD position on screen")


class TouchProofConfig(BaseModel):
    """Configuration for TouchProof multi-signal detection."""
    # Proximity thresholds (normalized)
    proximity_enter: float = Field(0.25, ge=0.0, le=1.0, description="Distance to consider close")
    proximity_exit: float = Field(0.40, ge=0.0, le=1.0, description="Distance to consider far")
    proximity_hard_cap: float = Field(0.50, ge=0.0, le=1.0, description="Auto-fail distance threshold")
    
    # Angle thresholds (degrees)
    angle_enter_deg: float = Field(20.0, ge=0.0, le=90.0, description="Max angle for parallel fingers")
    angle_exit_deg: float = Field(28.0, ge=0.0, le=90.0, description="Exit angle threshold")
    angle_hard_cap_deg: float = Field(45.0, ge=0.0, le=90.0, description="Auto-fail angle threshold")
    
    # Motion correlation
    correlation_frames: int = Field(5, ge=1, le=20, description="Frames for correlation window")
    correlation_min: float = Field(0.70, ge=0.0, le=1.0, description="Minimum correlation threshold")
    
    # Visibility/occlusion
    visibility_asymmetry_min: float = Field(0.12, ge=0.0, le=1.0, description="Min visibility asymmetry")
    
    
    # Temporal stability
    frames_to_enter: int = Field(3, ge=1, le=10, description="Frames to confirm touch")
    frames_to_exit: int = Field(3, ge=1, le=10, description="Frames to confirm release")
    
    # Fused score thresholds
    fused_enter_threshold: float = Field(0.8, ge=0.0, le=1.0, description="Fused score to trigger touch")
    fused_exit_threshold: float = Field(0.6, ge=0.0, le=1.0, description="Fused score to release touch")
    
    # Signal smoothing
    ema_alpha: float = Field(0.3, ge=0.0, le=1.0, description="EMA smoothing factor")
    smooth_proximity: bool = Field(True, description="Apply EMA to proximity signal")
    
    
    # Distance interaction parameters
    distance_near_px: float = Field(200.0, ge=50.0, le=500.0, description="Finger length when close")
    distance_far_px: float = Field(50.0, ge=10.0, le=200.0, description="Finger length when far")
    k_d: float = Field(0.30, ge=0.0, le=1.0, description="Proximity distance coefficient")
    k_theta: float = Field(4.0, ge=0.0, le=10.0, description="Angle distance coefficient")
    
    
    # MFC (Micro-Flow Cohesion) parameters
    mfc_window_frames: int = Field(5, ge=3, le=10, description="Optical flow history window")
    mfc_corr_min: float = Field(0.70, ge=0.0, le=1.0, description="Minimum correlation threshold")
    mfc_mag_ratio_min: float = Field(0.6, ge=0.0, le=1.0, description="Min magnitude ratio")
    mfc_mag_ratio_max: float = Field(1.4, ge=1.0, le=2.0, description="Max magnitude ratio")
    
    
    @model_validator(mode='after')
    def validate_thresholds(self) -> 'TouchProofConfig':
        """Validate that enter/exit thresholds are properly ordered."""
        if self.proximity_enter >= self.proximity_exit:
            raise ValueError("proximity_enter must be less than proximity_exit")
        if self.proximity_exit > self.proximity_hard_cap:
            raise ValueError("proximity_exit must be less than or equal to proximity_hard_cap")
        if self.angle_enter_deg >= self.angle_exit_deg:
            raise ValueError("angle_enter_deg must be less than angle_exit_deg")
        if self.angle_exit_deg > self.angle_hard_cap_deg:
            raise ValueError("angle_exit_deg must be less than or equal to angle_hard_cap_deg")
        if self.fused_exit_threshold >= self.fused_enter_threshold:
            raise ValueError("fused_exit_threshold must be less than fused_enter_threshold")
        return self



class AppConfig(BaseModel):
    """Main application configuration."""
    # Minimal runtime/env
    camera_index: int = Field(0, ge=0, description="Camera device index")
    frame_width: int = Field(960, ge=320, le=1920, description="Frame width in pixels")
    mirror: bool = Field(True, description="Mirror the camera feed")
    touch_threshold_pixels: float = Field(20.0, ge=5.0, le=100.0, description="Touch threshold in pixels")
    
    # Detection configs
    gates: GatesConfig = Field(default_factory=GatesConfig)
    kinematics: KinematicsConfig = Field(default_factory=KinematicsConfig)
    touchproof: TouchProofConfig = Field(default_factory=TouchProofConfig)
    scroll: ScrollConfig = Field(default_factory=ScrollConfig)
    
    @classmethod
    def from_yaml(cls, path: Optional[str]) -> "AppConfig":
        """Load configuration from YAML file."""
        if not path:
            return cls()
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            return cls(**data)
        except FileNotFoundError:
            return cls()
        except Exception as e:
            raise ValueError(f"Failed to load config from {path}: {e}")
    
    def to_yaml(self, path: str) -> None:
        """Save configuration to YAML file."""
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False, sort_keys=False)