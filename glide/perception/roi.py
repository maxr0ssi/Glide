from __future__ import annotations

from glide.core.types import Landmark


class StickyROI:
    def __init__(self, expansion: float = 1.5, decay_frames: int = 15) -> None:
        self.expansion = expansion
        self.decay_frames = decay_frames
        self._roi: tuple[int, int, int, int] | None = None  # x, y, w, h
        self._age: int = 0

    @staticmethod
    def _landmarks_bbox(
        landmarks: list[Landmark], width: int, height: int
    ) -> tuple[int, int, int, int]:
        xs = [int(l.x * width) for l in landmarks]
        ys = [int(l.y * height) for l in landmarks]
        x0, x1 = max(min(xs), 0), min(max(xs), width - 1)
        y0, y1 = max(min(ys), 0), min(max(ys), height - 1)
        w = max(1, x1 - x0)
        h = max(1, y1 - y0)
        return x0, y0, w, h

    def update(
        self,
        landmarks: list[Landmark],
        width: int,
        height: int,
        conf: float,
        conf_thresh: float = 0.7,
    ) -> tuple[int, int, int, int] | None:
        if conf >= conf_thresh:
            x, y, w, h = self._landmarks_bbox(landmarks, width, height)
            cx = x + w // 2
            cy = y + h // 2
            w = int(w * self.expansion)
            h = int(h * self.expansion)
            x = max(cx - w // 2, 0)
            y = max(cy - h // 2, 0)
            self._roi = (x, y, min(w, width - x), min(h, height - y))
            self._age = 0
        else:
            self._age += 1
            if self._age > self.decay_frames:
                self._roi = None
        return self._roi

    def contains(self, x: int, y: int) -> bool:
        if self._roi is None:
            return True
        rx, ry, rw, rh = self._roi
        return rx <= x <= rx + rw and ry <= y <= ry + rh

    @property
    def roi(self) -> tuple[int, int, int, int] | None:
        return self._roi
