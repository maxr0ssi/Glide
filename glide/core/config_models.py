"""Pydantic models for configuration validation."""

from pydantic import BaseModel, Field, field_validator, model_validator
import yaml


class GatesConfig(BaseModel):
    """Configuration for hand detection gates."""

    presence_conf: float = Field(
        0.7, ge=0.0, le=1.0, description="Minimum confidence for hand presence"
    )
    poses: list[str] = Field(
        default=["open_palm", "pointing_index", "two_up"], description="List of required poses"
    )
    pre_still_ms: int = Field(150, ge=0, description="Pre-stillness duration in milliseconds")
    max_idle_rms_speed: float = Field(
        0.08, ge=0.0, description="Maximum RMS speed for idle detection"
    )

    @field_validator("poses")
    @classmethod
    def validate_poses(cls, v: list[str]) -> list[str]:
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
    pixels_per_degree: float = Field(
        2.22, ge=0.1, le=10.0, description="Pixels per degree of rotation"
    )
    max_velocity: float = Field(
        100.0, ge=10.0, le=500.0, description="Maximum scroll velocity (pixels/event)"
    )
    acceleration_curve: float = Field(
        1.5, ge=1.0, le=3.0, description="Acceleration curve exponent"
    )
    respect_system_preference: bool = Field(
        True, description="Respect natural scrolling preference"
    )
    show_hud: bool = Field(True, description="Show HUD overlay")
    hud_fade_duration_ms: int = Field(500, ge=100, le=2000, description="HUD fade duration (ms)")
    hud_position: str = Field("bottom-right", description="HUD position on screen")

    # WebSocket HUD configuration
    hud_enabled: bool = Field(True, description="Enable WebSocket HUD broadcasting")
    hud_ws_port: int = Field(8765, ge=1024, le=65535, description="WebSocket port (localhost only)")
    hud_ws_token: str | None = Field(None, description="Security token (auto-generated if None)")
    hud_throttle_hz: int = Field(60, ge=30, le=120, description="WebSocket throttle rate in Hz")
    camera_throttle_hz: int = Field(
        30, ge=10, le=60, description="Camera frame throttle rate in Hz"
    )
    camera_frame_skip: int = Field(
        3, ge=1, le=10, description="Only publish every Nth camera frame"
    )


class OpticalFlowConfig(BaseModel):
    """Configuration for optical flow calculations."""

    window_frames: int = Field(5, ge=3, le=10, description="Optical flow history window")
    patch_size: int = Field(15, ge=5, le=30, description="Patch size for flow calculation")
    mfc_patch_size: int = Field(15, ge=5, le=30, description="Patch size for MFC flow calculation")


class TouchProofConfig(BaseModel):
    """Configuration for TouchProof multi-signal detection."""

    # Proximity thresholds (normalized)
    proximity_enter: float = Field(0.15, ge=0.0, le=1.0, description="Distance to consider close")
    proximity_exit: float = Field(0.25, ge=0.0, le=1.0, description="Distance to consider far")
    proximity_hard_cap: float = Field(
        0.70, ge=0.0, le=1.0, description="Auto-fail distance threshold"
    )

    # Angle thresholds (degrees)
    angle_enter_deg: float = Field(
        20.0, ge=0.0, le=90.0, description="Max angle for parallel fingers"
    )
    angle_exit_deg: float = Field(28.0, ge=0.0, le=90.0, description="Exit angle threshold")
    angle_hard_cap_deg: float = Field(
        45.0, ge=0.0, le=90.0, description="Auto-fail angle threshold"
    )

    # Motion correlation
    correlation_frames: int = Field(5, ge=1, le=20, description="Frames for correlation window")
    correlation_min: float = Field(
        0.70, ge=0.0, le=1.0, description="Minimum correlation threshold"
    )

    # Visibility/occlusion
    visibility_asymmetry_min: float = Field(
        0.12, ge=0.0, le=1.0, description="Min visibility asymmetry"
    )

    # Temporal stability
    frames_to_enter: int = Field(3, ge=1, le=10, description="Frames to confirm touch")
    frames_to_exit: int = Field(3, ge=1, le=10, description="Frames to confirm release")

    # Fused score thresholds
    fused_enter_threshold: float = Field(
        0.8, ge=0.0, le=1.0, description="Fused score to trigger touch"
    )
    fused_exit_threshold: float = Field(
        0.6, ge=0.0, le=1.0, description="Fused score to release touch"
    )

    # Signal smoothing
    ema_alpha: float = Field(0.3, ge=0.0, le=1.0, description="EMA smoothing factor")
    smooth_proximity: bool = Field(True, description="Apply EMA to proximity signal")

    # Proximity scoring mode
    proximity_mode: str = Field(
        "adaptive", description="Proximity scoring mode: fixed, adaptive, logarithmic"
    )
    baseline_learning_rate: float = Field(
        0.02, ge=0.001, le=0.1, description="Learning rate for baseline distances"
    )
    relative_touch_threshold: float = Field(
        0.85, ge=0.5, le=1.0, description="Relative distance for touch detection"
    )

    # Distance interaction parameters
    distance_near_px: float = Field(
        200.0, ge=50.0, le=500.0, description="Finger length when close"
    )
    distance_far_px: float = Field(50.0, ge=10.0, le=200.0, description="Finger length when far")
    k_d: float = Field(0.30, ge=0.0, le=1.0, description="Proximity distance coefficient")
    k_theta: float = Field(4.0, ge=0.0, le=10.0, description="Angle distance coefficient")

    # MFC (Micro-Flow Cohesion) parameters
    mfc_window_frames: int = Field(5, ge=3, le=10, description="Optical flow history window")
    mfc_patch_size: int = Field(15, ge=5, le=30, description="Patch size for MFC flow calculation")
    mfc_corr_min: float = Field(0.70, ge=0.0, le=1.0, description="Minimum correlation threshold")
    mfc_mag_ratio_min: float = Field(0.6, ge=0.0, le=1.0, description="Min magnitude ratio")
    mfc_mag_ratio_max: float = Field(1.4, ge=1.0, le=2.0, description="Max magnitude ratio")

    @model_validator(mode="after")
    def validate_thresholds(self) -> "TouchProofConfig":
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
    touch_threshold_pixels: float = Field(
        20.0, ge=5.0, le=100.0, description="Touch threshold in pixels"
    )

    # Detection configs
    gates: GatesConfig = Field(default_factory=GatesConfig)  # type: ignore[arg-type]
    kinematics: KinematicsConfig = Field(default_factory=KinematicsConfig)  # type: ignore[arg-type]
    touchproof: TouchProofConfig = Field(default_factory=TouchProofConfig)  # type: ignore[arg-type]
    scroll: ScrollConfig = Field(default_factory=ScrollConfig)  # type: ignore[arg-type]
    optical_flow: OpticalFlowConfig = Field(default_factory=OpticalFlowConfig)  # type: ignore[arg-type]

    @classmethod
    def from_yaml(cls, path: str | None) -> "AppConfig":
        """Load configuration from YAML file."""
        if not path:
            return cls()  # type: ignore[call-arg]

        # Deprecation warning for old config path
        if path == "glide/io/defaults.yaml":
            import warnings

            warnings.warn(
                "Config path 'glide/io/defaults.yaml' is deprecated. "
                "Please use 'configs/defaults.yaml' instead.",
                DeprecationWarning,
                stacklevel=2,
            )

        try:
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            return cls(**data)
        except FileNotFoundError:
            return cls()  # type: ignore[call-arg]
        except Exception as e:
            raise ValueError(f"Failed to load config from {path}: {e}")

    def to_yaml(self, path: str) -> None:
        """Save configuration to YAML file."""
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False, sort_keys=False)
