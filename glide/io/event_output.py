from __future__ import annotations

from typing import Deque, Optional
from collections import deque
import json
import sys

from glide.gestures.circular import CircularEvent


class JsonSink:
    def __init__(self, file_path: Optional[str] = None) -> None:
        self.file_path = file_path
        self._fp = open(file_path, "a", encoding="utf-8") if file_path else None

    def emit(self, event: CircularEvent) -> None:
        payload = json.dumps(event.to_json_dict(), separators=(",", ":"))
        if self._fp:
            self._fp.write(payload + "\n")
            self._fp.flush()
        else:
            sys.stdout.write(payload + "\n")
            sys.stdout.flush()

    def close(self) -> None:
        if self._fp:
            try:
                self._fp.close()
            except Exception:
                pass


class RingBufferLogger:
    def __init__(self, capacity: int = 256) -> None:
        self.capacity = capacity
        self._buf: Deque[CircularEvent] = deque(maxlen=capacity)

    def append(self, event: CircularEvent) -> None:
        self._buf.append(event)

    def dump_json(self) -> str:
        return "\n".join(json.dumps(e.to_json_dict(), separators=(",", ":")) for e in self._buf)


