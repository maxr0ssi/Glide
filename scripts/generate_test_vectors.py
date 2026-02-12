#!/usr/bin/env python3
"""Generate JSON test fixtures for cross-validating TypeScript ports.

Runs identical inputs through the Python scoring functions and outputs
deterministic JSON that the TS test suite can load.

Usage:
    python scripts/generate_test_vectors.py
"""

import json
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from glide.core.types import Landmark
from glide.features.poses import check_hand_pose
from glide.gestures.touchproof_scoring import (
    get_adaptive_weights,
    pearson_correlation,
    score_angle,
    score_proximity,
    score_visibility,
)

OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "apps",
    "web-ui",
    "tests",
    "fixtures",
)


def generate_scoring_fixtures():
    """Generate test vectors for scoring functions."""
    fixtures = {
        "scoreProximity": [],
        "scoreAngle": [],
        "scoreVisibility": [],
        "pearsonCorrelation": [],
        "getAdaptiveWeights": [],
    }

    # scoreProximity
    for dist in [0.0, 0.1, 0.25, 0.325, 0.40, 0.50, 0.80]:
        result = score_proximity(dist, 0.25, 0.40)
        fixtures["scoreProximity"].append(
            {
                "input": {"distanceNorm": dist, "enter": 0.25, "exit": 0.40},
                "expected": round(result, 6),
            }
        )

    # scoreAngle
    for angle in [0.0, 10.0, 24.0, 28.0, 32.0, 45.0]:
        result = score_angle(angle, 24.0, 32.0)
        fixtures["scoreAngle"].append(
            {
                "input": {"angleDeg": angle, "enter": 24.0, "exit": 32.0},
                "expected": round(result, 6),
            }
        )

    # scoreVisibility
    test_cases = [
        (None, None, 0.12),
        (0.9, 0.7, 0.12),
        (0.9, 0.84, 0.12),
        (0.5, 0.5, 0.12),
    ]
    for vis_a, vis_b, asym_min in test_cases:
        lm_a = Landmark(x=0, y=0, visibility=vis_a)
        lm_b = Landmark(x=0, y=0, visibility=vis_b)
        result = score_visibility(lm_a, lm_b, asym_min)
        fixtures["scoreVisibility"].append(
            {
                "input": {"visA": vis_a, "visB": vis_b, "asymmetryMin": asym_min},
                "expected": round(result, 6),
            }
        )

    # pearsonCorrelation
    corr_cases = [
        ([1, 2, 3, 4], [2, 4, 6, 8]),
        ([1, 2, 3, 4], [8, 6, 4, 2]),
        ([5, 5, 5], [3, 3, 3]),
        ([1, 2, 3], [5, 5, 5]),
    ]
    for a, b in corr_cases:
        result = pearson_correlation(a, b)
        fixtures["pearsonCorrelation"].append(
            {
                "input": {"a": a, "b": b},
                "expected": round(result, 6) if result is not None else None,
            }
        )

    # getAdaptiveWeights
    for df in [0.0, 0.3, 0.5, 0.7, 1.0]:
        weights = get_adaptive_weights(df)
        fixtures["getAdaptiveWeights"].append(
            {
                "input": {"distanceFactor": df},
                "expected": {k: round(v, 6) for k, v in weights.items()},
            }
        )

    return fixtures


def generate_pose_fixtures():
    """Generate test vectors for pose detection."""
    fixtures = []

    # Default landmarks (21 points)
    base_landmarks = [
        Landmark(x=0.50, y=0.70),  # 0: wrist
        Landmark(x=0.48, y=0.65),  # 1
        Landmark(x=0.44, y=0.60),  # 2
        Landmark(x=0.42, y=0.55),  # 3
        Landmark(x=0.40, y=0.50),  # 4
        Landmark(x=0.48, y=0.55),  # 5: index MCP
        Landmark(x=0.47, y=0.48),  # 6
        Landmark(x=0.46, y=0.42),  # 7
        Landmark(x=0.45, y=0.35),  # 8: index tip
        Landmark(x=0.52, y=0.54),  # 9: middle MCP
        Landmark(x=0.52, y=0.46),  # 10
        Landmark(x=0.52, y=0.40),  # 11
        Landmark(x=0.52, y=0.33),  # 12: middle tip
        Landmark(x=0.56, y=0.56),  # 13: ring MCP
        Landmark(x=0.57, y=0.50),  # 14
        Landmark(x=0.58, y=0.45),  # 15
        Landmark(x=0.58, y=0.40),  # 16: ring tip
        Landmark(x=0.60, y=0.60),  # 17: pinky MCP
        Landmark(x=0.61, y=0.55),  # 18
        Landmark(x=0.62, y=0.52),  # 19
        Landmark(x=0.63, y=0.50),  # 20
    ]

    flags = check_hand_pose(base_landmarks)
    fixtures.append(
        {
            "name": "default_hand",
            "landmarks": [{"x": lm.x, "y": lm.y} for lm in base_landmarks],
            "expected": {
                "openPalm": flags.open_palm,
                "pointingIndex": flags.pointing_index,
                "twoUp": flags.two_up,
            },
        }
    )

    return fixtures


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    scoring = generate_scoring_fixtures()
    with open(os.path.join(OUTPUT_DIR, "scoring.json"), "w") as f:
        json.dump(scoring, f, indent=2)

    poses = generate_pose_fixtures()
    with open(os.path.join(OUTPUT_DIR, "poses.json"), "w") as f:
        json.dump(poses, f, indent=2)

    print(f"Generated test fixtures in {OUTPUT_DIR}")
    print(f"  scoring.json: {sum(len(v) for v in scoring.values())} test vectors")
    print(f"  poses.json: {len(poses)} test vectors")


if __name__ == "__main__":
    main()
