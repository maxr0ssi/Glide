from __future__ import annotations

from typing import List

from glide.core.types import Landmark, PoseFlags


def check_hand_pose(landmarks: List[Landmark]) -> PoseFlags:
    """Check hand pose for common gestures.

    - open_palm: spread between index MCP and pinky MCP is large
    - pointing_index: index tip beyond middle tip in pointing direction (rough proxy)
    - two_up: index and middle tips above ring tip (y smaller in image coords)
    """
    flags = PoseFlags()
    if not landmarks or len(landmarks) < 21:
        return flags
    # MediaPipe indexing: 5=index MCP, 9=middle MCP, 13=ring MCP, 17=pinky MCP
    # Tips: 8=index tip, 12=middle tip, 16=ring tip
    index_mcp = landmarks[5]
    pinky_mcp = landmarks[17]
    index_tip = landmarks[8]
    middle_tip = landmarks[12]
    ring_tip = landmarks[16]

    spread = abs(index_mcp.x - pinky_mcp.x)
    flags.open_palm = spread > 0.12

    flags.pointing_index = (index_tip.y < middle_tip.y - 0.02)

    flags.two_up = (index_tip.y < ring_tip.y - 0.02) and (middle_tip.y < ring_tip.y - 0.02)

    return flags


