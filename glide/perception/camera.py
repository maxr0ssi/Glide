from __future__ import annotations

import time

import cv2

from glide.core.contracts import Frame, FrameSource


class Camera(FrameSource):
    def __init__(
        self, index: int = 0, width: int = 960, mirror: bool = True, fps_cap: float | None = None
    ) -> None:
        self.index = index
        self.width = width
        self.mirror = mirror
        self.fps_cap = fps_cap
        self._cap = cv2.VideoCapture(index)
        if width:
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, float(width))
        self._last_ts = 0.0

    def read(self) -> Frame | None:
        if not self._cap.isOpened():
            return None
        ok, img = self._cap.read()
        if not ok or img is None:
            return None
        if self.mirror:
            img = cv2.flip(img, 1)
        h, w = img.shape[:2]
        now = int(time.time() * 1000)
        if self.fps_cap is not None and self._last_ts > 0:
            dt = (now - self._last_ts) / 1000.0
            min_dt = 1.0 / max(self.fps_cap, 1e-6)
            if dt < min_dt:
                time.sleep(max(min_dt - dt, 0))
                now = int(time.time() * 1000)
        self._last_ts = now
        return Frame(image=img, timestamp_ms=now)

    def release(self) -> None:
        self._cap.release()
