"""Pure scoring functions for TouchProof detection.

All functions are stateless and side-effect free, making them easy to test and reason about.
"""

from __future__ import annotations

import math
from collections import deque

import numpy as np

from glide.core.config_models import TouchProofConfig
from glide.core.types import Landmark


def score_proximity(distance_norm: float, enter_threshold: float, exit_threshold: float) -> float:
    """Convert normalized distance to proximity score (0-1).

    Args:
        distance_norm: Normalized distance between fingertips
        enter_threshold: Distance threshold to trigger touch
        exit_threshold: Distance threshold to release touch

    Returns:
        Proximity score from 0 (far) to 1 (close)
    """
    # Closer = higher score
    # Use smooth transition between enter and exit thresholds
    if distance_norm <= enter_threshold:
        return 1.0
    if distance_norm >= exit_threshold:
        return 0.0
    # Linear interpolation
    range_size = exit_threshold - enter_threshold
    return 1.0 - (distance_norm - enter_threshold) / range_size


def score_angle(angle_deg: float, enter_deg: float, exit_deg: float) -> float:
    """Convert angle to score (0-1).

    Args:
        angle_deg: Angle between fingertip directions (degrees)
        enter_deg: Angle threshold to trigger touch
        exit_deg: Angle threshold to release touch

    Returns:
        Angle score from 0 (divergent) to 1 (parallel)
    """
    # More parallel = higher score
    if angle_deg <= enter_deg:
        return 1.0
    if angle_deg >= exit_deg:
        return 0.0
    range_size = exit_deg - enter_deg
    return 1.0 - (angle_deg - enter_deg) / range_size


def score_visibility(index_tip: Landmark, middle_tip: Landmark, asymmetry_min: float) -> float:
    """Score based on visibility asymmetry (occlusion indicator).

    Args:
        index_tip: Index finger tip landmark
        middle_tip: Middle finger tip landmark
        asymmetry_min: Minimum asymmetry to consider touching

    Returns:
        Visibility score from 0 to 1
    """
    if index_tip.visibility is None or middle_tip.visibility is None:
        return 0.5  # Neutral if no visibility data

    # When fingers overlap, one typically has lower visibility
    asymmetry = abs(index_tip.visibility - middle_tip.visibility)

    if asymmetry >= asymmetry_min:
        return 1.0
    return asymmetry / asymmetry_min


def compute_correlation(
    idx_positions: deque[tuple[float, float]],
    mid_positions: deque[tuple[float, float]],
    correlation_frames: int,
    correlation_min: float,
) -> float:
    """Compute velocity correlation between fingers.

    Args:
        idx_positions: Recent index finger positions
        mid_positions: Recent middle finger positions
        correlation_frames: Number of frames needed
        correlation_min: Minimum correlation to consider touching

    Returns:
        Correlation score from 0 to 1
    """
    if len(idx_positions) < correlation_frames:
        return 0.5  # Neutral until we have enough data

    # Compute velocities
    idx_vels = []
    mid_vels = []

    for i in range(1, len(idx_positions)):
        # Index finger velocity
        dx_idx = idx_positions[i][0] - idx_positions[i - 1][0]
        dy_idx = idx_positions[i][1] - idx_positions[i - 1][1]
        idx_vels.append((dx_idx, dy_idx))

        # Middle finger velocity
        dx_mid = mid_positions[i][0] - mid_positions[i - 1][0]
        dy_mid = mid_positions[i][1] - mid_positions[i - 1][1]
        mid_vels.append((dx_mid, dy_mid))

    # Compute correlation for x and y separately
    idx_vx = [v[0] for v in idx_vels]
    idx_vy = [v[1] for v in idx_vels]
    mid_vx = [v[0] for v in mid_vels]
    mid_vy = [v[1] for v in mid_vels]

    corr_x = pearson_correlation(idx_vx, mid_vx)
    corr_y = pearson_correlation(idx_vy, mid_vy)

    # Average correlation
    if corr_x is not None and corr_y is not None:
        avg_corr = (corr_x + corr_y) / 2.0
    elif corr_x is not None:
        avg_corr = corr_x
    elif corr_y is not None:
        avg_corr = corr_y
    else:
        avg_corr = 0.5

    # Convert to 0-1 score
    if avg_corr >= correlation_min:
        return 1.0
    return max(0.0, avg_corr)


def pearson_correlation(a: list[float], b: list[float]) -> float | None:
    """Calculate Pearson correlation coefficient.

    Args:
        a: First data series
        b: Second data series

    Returns:
        Correlation coefficient (-1 to 1) or None if cannot compute
    """
    n = min(len(a), len(b))
    if n < 2:
        return None

    mean_a = sum(a) / n
    mean_b = sum(b) / n

    # Handle constant series
    var_a = sum((x - mean_a) ** 2 for x in a)
    var_b = sum((x - mean_b) ** 2 for x in b)

    if var_a < 1e-9 or var_b < 1e-9:
        return 1.0 if var_a < 1e-9 and var_b < 1e-9 else 0.0

    cov = sum((a[i] - mean_a) * (b[i] - mean_b) for i in range(n))
    return cov / math.sqrt(var_a * var_b)


def score_proximity_adjusted(
    distance_norm: float,
    distance_factor: float,
    config: TouchProofConfig,
    baseline: float | None,
) -> float:
    """Score proximity with distance-aware thresholds and relative baseline.

    Args:
        distance_norm: Normalized distance between fingertips
        distance_factor: Camera distance factor (0=close, 1=far)
        config: TouchProof configuration
        baseline: Expected baseline distance (for adaptive mode)

    Returns:
        Adjusted proximity score from 0 to 1
    """
    # Mode-based scoring
    if config.proximity_mode == "adaptive":
        # Try relative scoring if baselines are available
        if baseline is not None:
            # Relative proximity: how much closer than usual?
            relative_proximity = baseline / (distance_norm + 0.001)  # Avoid division by zero

            # Sigmoid scoring centered at threshold
            center = config.relative_touch_threshold
            steepness = 6.0
            score = 1.0 / (1.0 + np.exp(-steepness * (relative_proximity - center)))
            return float(score)

    # Fallback to threshold-based scoring with distance adjustment
    k_d = getattr(config, "k_d", 0.3)  # Use config value
    # Stricter when far (distance_factor=1), looser when close (0)
    enter_adjusted = config.proximity_enter * (1 + k_d * distance_factor)
    exit_adjusted = config.proximity_exit * (1 + k_d * distance_factor)

    # Score with adjusted thresholds
    if distance_norm <= enter_adjusted:
        return 1.0
    if distance_norm >= exit_adjusted:
        return 0.0
    range_size = exit_adjusted - enter_adjusted
    return 1.0 - (distance_norm - enter_adjusted) / range_size


def score_angle_adjusted(
    angle_deg: float, distance_factor: float, config: TouchProofConfig
) -> float:
    """Score angle with distance-aware thresholds.

    Args:
        angle_deg: Angle between fingertip directions (degrees)
        distance_factor: Camera distance factor (0=close, 1=far)
        config: TouchProof configuration

    Returns:
        Adjusted angle score from 0 to 1
    """
    # Adjust thresholds: stricter (smaller) when close
    k_theta = getattr(config, "k_theta", 4.0)  # Angle interaction coefficient
    enter_adjusted = config.angle_enter_deg - k_theta * (1 - distance_factor)
    exit_adjusted = config.angle_exit_deg - k_theta * (1 - distance_factor)

    # Score with adjusted thresholds
    if angle_deg <= enter_adjusted:
        return 1.0
    if angle_deg >= exit_adjusted:
        return 0.0
    range_size = exit_adjusted - enter_adjusted
    return 1.0 - (angle_deg - enter_adjusted) / range_size


def get_adaptive_weights(distance_factor: float) -> dict[str, float]:
    """Get fusion weights based on hand distance.

    Args:
        distance_factor: Camera distance factor (0=close, 1=far)

    Returns:
        Dictionary of signal weights (proximity, angle, mfc, occlusion)
    """
    if distance_factor > 0.7:  # Far away
        return {"proximity": 0.45, "angle": 0.20, "mfc": 0.30, "occlusion": 0.05}
    if distance_factor < 0.3:  # Very close - reduced angle weight for laptop cameras
        return {"proximity": 0.40, "angle": 0.30, "mfc": 0.25, "occlusion": 0.05}
    # Interpolate
    # Linear interpolation between near and far weights
    t = (distance_factor - 0.3) / 0.4  # Map [0.3, 0.7] to [0, 1]
    near_weights = {"proximity": 0.40, "angle": 0.30, "mfc": 0.25, "occlusion": 0.05}
    far_weights = {"proximity": 0.45, "angle": 0.20, "mfc": 0.30, "occlusion": 0.05}
    return {k: near_weights[k] * (1 - t) + far_weights[k] * t for k in near_weights}
