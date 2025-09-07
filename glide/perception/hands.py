from __future__ import annotations

import os

import cv2
import mediapipe as mp
import numpy as np

from glide.core.types import HandDet, Landmark

try:
    # Prefer MediaPipe Tasks
    from mediapipe.tasks import python as mp_tasks
    from mediapipe.tasks.python import vision

    _HAVE_TASKS = True
except ImportError:
    _HAVE_TASKS = False

try:
    # Fallback: classic MediaPipe Solutions
    from mediapipe.solutions import hands as mp_hands

    _HAVE_SOLUTIONS = True
except ImportError:
    _HAVE_SOLUTIONS = False


class HandLandmarker:
    def __init__(
        self, model_path: str | None = None, num_hands: int = 1, min_conf: float = 0.5
    ) -> None:
        self.num_hands = num_hands
        self.min_conf = min_conf
        self._init_tasks(model_path)
        if self._detector is None:
            self._init_solutions()

    def _init_tasks(self, model_path: str | None) -> None:
        self._detector = None
        if not _HAVE_TASKS:
            return
        # Try default model if not provided
        if model_path is None:
            root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
            default_path = os.path.join(root, "models", "hand_landmarker.task")
            model_path = default_path if os.path.exists(default_path) else None
        if model_path is None:
            import sys

            sys.stderr.write(
                "Warning: No hand tracking model found. Use --model to specify model path.\n"
            )
        base_options = (
            mp_tasks.BaseOptions(model_asset_path=model_path)
            if model_path
            else mp_tasks.BaseOptions()
        )
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=self.num_hands,
            min_hand_detection_confidence=self.min_conf,
            min_hand_presence_confidence=self.min_conf,
            min_tracking_confidence=self.min_conf,
        )
        try:
            self._detector = vision.HandLandmarker.create_from_options(options)
        except (RuntimeError, ValueError) as e:
            import sys

            sys.stderr.write(f"Warning: Failed to initialize hand landmarker: {e}\n")
            self._detector = None

    def _init_solutions(self) -> None:
        self._solutions = None
        if not _HAVE_SOLUTIONS:
            import sys

            sys.stderr.write("Error: MediaPipe not available. Hand detection disabled.\n")
            return
        try:
            self._solutions = mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=self.num_hands,
                min_detection_confidence=self.min_conf,
                min_tracking_confidence=self.min_conf,
                model_complexity=0,
            )
            # Using MediaPipe Solutions Hands as fallback
        except (RuntimeError, ValueError) as e:
            self._solutions = None
            import sys

            sys.stderr.write(f"Error: Failed to initialize hand tracking: {e}\n")

    def detect(self, image_bgr: np.ndarray) -> HandDet | None:
        # Tasks path
        if self._detector is not None:
            image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
            mpimg = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
            result = self._detector.detect(mpimg)
            if not result or not result.hand_landmarks or len(result.hand_landmarks) == 0:
                return None
            lmks = result.hand_landmarks[0]
            handedness = result.handedness[0][0].category_name if result.handedness else "Unknown"
            score = result.handedness[0][0].score if result.handedness else 0.0
            landmarks_task: list[Landmark] = [
                Landmark(
                    x=pt.x,
                    y=pt.y,
                    visibility=pt.visibility if hasattr(pt, "visibility") else None,
                    presence=pt.presence if hasattr(pt, "presence") else None,
                )
                for pt in lmks
            ]
            return HandDet(
                landmarks=landmarks_task, handedness=handedness, confidence=float(score), bbox=None
            )

        # Solutions fallback
        if hasattr(self, "_solutions") and self._solutions is not None:
            image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
            res = self._solutions.process(image_rgb)
            if not res or not res.multi_hand_landmarks or len(res.multi_hand_landmarks) == 0:
                return None
            lmks = res.multi_hand_landmarks[0].landmark
            handedness = "Unknown"
            score = 0.0
            try:
                if res.multi_handedness and len(res.multi_handedness) > 0:
                    handedness = res.multi_handedness[0].classification[0].label
                    score = float(res.multi_handedness[0].classification[0].score)
            except (IndexError, AttributeError):
                pass  # Keep defaults if handedness data is missing
            landmarks_list: list[Landmark] = [
                Landmark(
                    x=pt.x,
                    y=pt.y,
                    visibility=pt.visibility if hasattr(pt, "visibility") else None,
                    presence=pt.presence if hasattr(pt, "presence") else None,
                )
                for pt in lmks
            ]
            return HandDet(
                landmarks=landmarks_list, handedness=handedness, confidence=score, bbox=None
            )

        return None
