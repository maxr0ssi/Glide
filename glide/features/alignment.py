from __future__ import annotations

import math

import numpy as np

from glide.core.types import Landmark


class HandAligner:
    """Handles coordinate transformations between image space and hand-aligned space."""

    def __init__(self) -> None:
        self.palm_center: tuple[float, float] | None = None
        self.theta_rad: float | None = None
        self.scale: float | None = None
        self.image_width: int | None = None
        self.image_height: int | None = None

    def update(self, landmarks: list[Landmark], image_width: int, image_height: int) -> bool:
        """
        Update alignment parameters from hand landmarks.
        Returns True if successful, False otherwise.
        """
        if not landmarks or len(landmarks) < 21:
            return False

        self.image_width = image_width
        self.image_height = image_height

        # Calculate palm center (mean of wrist + MCPs)
        wrist = landmarks[0]
        mcps = [landmarks[i] for i in (5, 9, 13, 17)]  # Index, middle, ring, pinky MCPs

        palm_points = [(wrist.x, wrist.y)] + [(mcp.x, mcp.y) for mcp in mcps]
        palm_x = sum(p[0] for p in palm_points) / len(palm_points)
        palm_y = sum(p[1] for p in palm_points) / len(palm_points)
        self.palm_center = (palm_x, palm_y)

        # Calculate hand orientation (wrist to middle MCP)
        middle_mcp = landmarks[9]
        dx = middle_mcp.x - wrist.x
        dy = middle_mcp.y - wrist.y
        self.theta_rad = math.atan2(dy, dx)

        # Calculate scale (index finger length)
        index_tip = landmarks[8]
        index_mcp = landmarks[5]
        finger_length = math.hypot(index_tip.x - index_mcp.x, index_tip.y - index_mcp.y)
        self.scale = max(finger_length, 0.001)  # Avoid division by zero

        return True

    def normalized_to_pixel(self, x_norm: float, y_norm: float) -> tuple[int, int]:
        """
        Convert normalized coordinates (0-1) to pixel coordinates.

        Args:
            x_norm: X coordinate in normalized space (0-1)
            y_norm: Y coordinate in normalized space (0-1)

        Returns:
            Tuple of (x, y) in pixel coordinates
        """
        if self.image_width is None or self.image_height is None:
            return (0, 0)

        x_px = int(x_norm * self.image_width)
        y_px = int(y_norm * self.image_height)
        return (x_px, y_px)

    def pixel_to_normalized(self, x_px: int, y_px: int) -> tuple[float, float]:
        """
        Convert pixel coordinates to normalized coordinates (0-1).

        Args:
            x_px: X coordinate in pixels
            y_px: Y coordinate in pixels

        Returns:
            Tuple of (x, y) in normalized coordinates (0-1)
        """
        if self.image_width is None or self.image_height is None:
            return (0.0, 0.0)

        x_norm = x_px / self.image_width
        y_norm = y_px / self.image_height
        return (x_norm, y_norm)

    def to_hand_aligned(self, x_norm: float, y_norm: float) -> tuple[float, float]:
        """
        Transform normalized coordinates to hand-aligned coordinates.
        Origin at palm center, rotated to align with hand, scaled by finger length.
        """
        if self.palm_center is None or self.theta_rad is None or self.scale is None:
            return (0.0, 0.0)

        # Translate to palm-centered
        x_rel = x_norm - self.palm_center[0]
        y_rel = y_norm - self.palm_center[1]

        # Rotate to align with hand
        cos_theta = math.cos(-self.theta_rad)
        sin_theta = math.sin(-self.theta_rad)
        x_aligned = cos_theta * x_rel - sin_theta * y_rel
        y_aligned = sin_theta * x_rel + cos_theta * y_rel

        # Scale by finger length
        x_scaled = x_aligned / self.scale
        y_scaled = y_aligned / self.scale

        return (x_scaled, y_scaled)

    def from_hand_aligned(self, x_aligned: float, y_aligned: float) -> tuple[float, float]:
        """
        Transform hand-aligned coordinates back to normalized coordinates.
        """
        if self.palm_center is None or self.theta_rad is None or self.scale is None:
            return (0.0, 0.0)

        # Unscale
        x_rel = x_aligned * self.scale
        y_rel = y_aligned * self.scale

        # Rotate back
        cos_theta = math.cos(self.theta_rad)
        sin_theta = math.sin(self.theta_rad)
        x_norm_rel = cos_theta * x_rel - sin_theta * y_rel
        y_norm_rel = sin_theta * x_rel + cos_theta * y_rel

        # Translate back
        x_norm = x_norm_rel + self.palm_center[0]
        y_norm = y_norm_rel + self.palm_center[1]

        return (x_norm, y_norm)

    def to_hand_aligned_pixel(self, x_px: int, y_px: int) -> tuple[float, float]:
        """
        Convert pixel coordinates directly to hand-aligned coordinates.

        Args:
            x_px: X coordinate in pixels
            y_px: Y coordinate in pixels

        Returns:
            Tuple of (x, y) in hand-aligned coordinates
        """
        x_norm, y_norm = self.pixel_to_normalized(x_px, y_px)
        return self.to_hand_aligned(x_norm, y_norm)

    def from_hand_aligned_to_pixel(self, x_aligned: float, y_aligned: float) -> tuple[int, int]:
        """
        Convert hand-aligned coordinates directly to pixel coordinates.

        Args:
            x_aligned: X coordinate in hand-aligned space
            y_aligned: Y coordinate in hand-aligned space

        Returns:
            Tuple of (x, y) in pixel coordinates
        """
        x_norm, y_norm = self.from_hand_aligned(x_aligned, y_aligned)
        return self.normalized_to_pixel(x_norm, y_norm)

    def get_fingertip_pixels(
        self, landmarks: list[Landmark]
    ) -> tuple[tuple[int, int], tuple[int, int]]:
        """
        Get index and middle fingertip positions in pixel coordinates.

        Args:
            landmarks: List of 21 hand landmarks

        Returns:
            Tuple of ((index_x, index_y), (middle_x, middle_y)) in pixels
        """
        if not landmarks or len(landmarks) < 21:
            return ((0, 0), (0, 0))

        index_tip = landmarks[8]
        middle_tip = landmarks[12]

        index_px = self.normalized_to_pixel(index_tip.x, index_tip.y)
        middle_px = self.normalized_to_pixel(middle_tip.x, middle_tip.y)

        return (index_px, middle_px)

    def get_normalized_distance(self, landmarks: list[Landmark]) -> float:
        """
        Get distance between index and middle fingertips normalized by finger length.

        Args:
            landmarks: List of 21 hand landmarks

        Returns:
            Normalized distance (0.0 = touching, 1.0 = one finger length apart)
        """
        if not landmarks or len(landmarks) < 21 or self.scale is None:
            return float("inf")

        index_tip = landmarks[8]
        middle_tip = landmarks[12]

        # Convert to hand-aligned coordinates
        idx_aligned = self.to_hand_aligned(index_tip.x, index_tip.y)
        mid_aligned = self.to_hand_aligned(middle_tip.x, middle_tip.y)

        # Calculate distance (already normalized by scale)
        distance = math.hypot(idx_aligned[0] - mid_aligned[0], idx_aligned[1] - mid_aligned[1])

        return distance

    def get_normalized_distance_log(self, landmarks: list[Landmark]) -> float:
        """
        Get log-normalized distance between fingertips.
        More stable across different camera distances.

        Returns:
            Log-normalized distance (0.0 = touching, higher = farther)
        """
        if not landmarks or len(landmarks) < 21:
            return float("inf")

        index_tip = landmarks[8]
        middle_tip = landmarks[12]

        # Get pixel distance
        index_px = self.normalized_to_pixel(index_tip.x, index_tip.y)
        middle_px = self.normalized_to_pixel(middle_tip.x, middle_tip.y)

        distance_px = math.hypot(index_px[0] - middle_px[0], index_px[1] - middle_px[1])

        # Reference distance (typical finger width in pixels at medium distance)
        reference_px = 30.0

        # Log normalization: log(1 + d) / log(1 + ref)
        # This compresses large distances and expands small ones
        distance_log = np.log(1 + distance_px) / np.log(1 + reference_px)

        return float(distance_log)

    def get_fingertip_angle(self, landmarks: list[Landmark]) -> float:
        """
        Get angle between index and middle fingers from palm center (degrees).

        Args:
            landmarks: List of 21 hand landmarks

        Returns:
            Angle in degrees (0 = parallel, 90 = perpendicular)
        """
        if not landmarks or len(landmarks) < 21:
            return 0.0

        index_tip = landmarks[8]
        middle_tip = landmarks[12]

        # Convert to hand-aligned coordinates
        idx_aligned = self.to_hand_aligned(index_tip.x, index_tip.y)
        mid_aligned = self.to_hand_aligned(middle_tip.x, middle_tip.y)

        # Calculate vectors from origin (palm center in aligned space)
        idx_len = math.hypot(idx_aligned[0], idx_aligned[1])
        mid_len = math.hypot(mid_aligned[0], mid_aligned[1])

        if idx_len < 1e-6 or mid_len < 1e-6:
            return 0.0

        # Dot product for angle
        dot = idx_aligned[0] * mid_aligned[0] + idx_aligned[1] * mid_aligned[1]
        cos_angle = dot / (idx_len * mid_len)
        cos_angle = max(-1.0, min(1.0, cos_angle))  # Clamp for safety

        angle_rad = math.acos(cos_angle)
        angle_deg = math.degrees(angle_rad)

        return angle_deg

    def get_hand_distance_factor(self) -> float:
        """Get distance factor: 0.0 = very close, 1.0 = far away.

        Uses finger length in pixels as a proxy for hand distance.
        Typical ranges: 200px = close, 50px = far
        """
        if self.scale is None or self.image_width is None or self.image_height is None:
            return 0.5  # Default to medium distance

        # Get finger length in pixels
        finger_px = self.scale * max(self.image_width, self.image_height)

        # Map to distance factor
        # 200px or more = 0.0 (very close)
        # 50px or less = 1.0 (far away)
        distance_factor = np.clip((200 - finger_px) / 150, 0, 1)

        return float(distance_factor)

    def get_finger_length_pixels(self) -> float:
        """
        Get the finger length in pixels.

        Returns:
            Index finger length in pixels
        """
        if self.scale is None or self.image_width is None or self.image_height is None:
            return 100.0  # Default

        return self.scale * max(self.image_width, self.image_height)
