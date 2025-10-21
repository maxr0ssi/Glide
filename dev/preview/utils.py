"""Visualization utilities for display purposes."""

from glide.core.types import Landmark


def get_pixel_distance(
    landmarks: list[Landmark], width: int, height: int
) -> tuple[float, tuple[int, int], tuple[int, int]]:
    """
    Get pixel distance between index and middle fingertips.
    Used only for visualization, not for detection logic.

    Returns:
        Tuple of (distance_pixels, index_tip_coords, middle_tip_coords)
    """
    if len(landmarks) < 21:
        return 0.0, (0, 0), (0, 0)

    # Index fingertip (landmark 8)
    index_tip = landmarks[8]
    index_x = int(index_tip.x * width)
    index_y = int(index_tip.y * height)

    # Middle fingertip (landmark 12)
    middle_tip = landmarks[12]
    middle_x = int(middle_tip.x * width)
    middle_y = int(middle_tip.y * height)

    # Calculate pixel distance
    dx = index_x - middle_x
    dy = index_y - middle_y
    distance = (dx**2 + dy**2) ** 0.5

    return distance, (index_x, index_y), (middle_x, middle_y)
