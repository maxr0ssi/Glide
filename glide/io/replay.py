"""Record and replay functionality for testing without a camera.

This module provides functions to:
1. Record frames, landmarks, and events to JSONL files
2. Replay recorded sessions for testing and debugging
"""

import json
import time
from typing import Iterator, Optional, Dict, Any, List
from pathlib import Path
import numpy as np
import cv2

from glide.core.contracts import Frame, FrameSource
from glide.core.types import Landmark, HandDet
from glide.gestures.circular import CircularEvent


class ReplayFrame:
    """Container for replayed frame data."""
    def __init__(self, frame: Frame, landmarks: Optional[HandDet] = None, 
                 events: Optional[List[CircularEvent]] = None):
        self.frame = frame
        self.landmarks = landmarks
        self.events = events or []


class ReplaySource(FrameSource):
    """Frame source that replays from a recorded session."""
    
    def __init__(self, replay_path: str):
        self.path = Path(replay_path)
        self.frames: List[ReplayFrame] = []
        self.current_index = 0
        self._load_replay()
    
    def _load_replay(self) -> None:
        """Load replay data from JSONL file."""
        with open(self.path, 'r') as f:
            for line in f:
                data = json.loads(line)
                
                # Reconstruct frame
                if 'frame' in data:
                    # If frame was saved as base64, decode it
                    # For now, create a dummy frame
                    frame = Frame(
                        image=np.zeros((480, 640, 3), dtype=np.uint8),
                        timestamp_ms=data['timestamp_ms']
                    )
                else:
                    frame = None
                
                # Reconstruct landmarks
                if 'landmarks' in data and data['landmarks']:
                    landmarks_list = [
                        Landmark(
                            x=lm['x'], 
                            y=lm['y'],
                            visibility=lm.get('visibility'),
                            presence=lm.get('presence')
                        )
                        for lm in data['landmarks']
                    ]
                    hand_det = HandDet(
                        landmarks=landmarks_list,
                        handedness=data.get('handedness', 'Right'),
                        confidence=data.get('confidence', 1.0)
                    )
                else:
                    hand_det = None
                
                # Reconstruct events
                events = []
                if 'events' in data:
                    # Convert event dicts back to SwishEvent objects
                    # This is simplified - would need proper deserialization
                    events = data['events']
                
                self.frames.append(ReplayFrame(frame, hand_det, events))
    
    def read(self) -> Optional[Frame]:
        """Read next frame from replay."""
        if self.current_index >= len(self.frames):
            return None
        
        replay_frame = self.frames[self.current_index]
        self.current_index += 1
        
        # Simulate real-time playback by checking timestamps
        if self.current_index > 1:
            prev_ts = self.frames[self.current_index - 2].frame.timestamp_ms
            curr_ts = replay_frame.frame.timestamp_ms
            delay_ms = curr_ts - prev_ts
            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)
        
        return replay_frame.frame
    
    def release(self) -> None:
        """Clean up resources."""
        self.frames.clear()
        self.current_index = 0


def record_session(output_path: str) -> 'SessionRecorder':
    """Create a session recorder.
    
    Usage:
        recorder = record_session('test_session.jsonl')
        # ... run detection pipeline ...
        recorder.add_frame(frame, landmarks, events)
        recorder.close()
    """
    return SessionRecorder(output_path)


class SessionRecorder:
    """Records frames, landmarks, and events to JSONL."""
    
    def __init__(self, output_path: str):
        self.path = Path(output_path)
        self.file = open(self.path, 'w')
    
    def add_frame(self, frame: Frame, landmarks: Optional[HandDet] = None,
                  events: Optional[List[CircularEvent]] = None) -> None:
        """Record a frame with its detection results."""
        record = {
            'timestamp_ms': frame.timestamp_ms,
            'frame_shape': frame.image.shape,
        }
        
        # Optionally save frame as base64 or just metadata
        # For large recordings, might want to save video separately
        
        if landmarks:
            record['landmarks'] = [
                {
                    'x': lm.x,
                    'y': lm.y,
                    'visibility': lm.visibility,
                    'presence': lm.presence
                }
                for lm in landmarks.landmarks
            ]
            record['handedness'] = landmarks.handedness
            record['confidence'] = landmarks.confidence
        
        if events:
            record['events'] = [event.to_json_dict() for event in events]
        
        self.file.write(json.dumps(record) + '\n')
    
    def close(self) -> None:
        """Close the recording file."""
        self.file.close()


def replay_session(replay_path: str) -> Iterator[ReplayFrame]:
    """Iterate through a recorded session.
    
    Yields:
        ReplayFrame objects containing frame, landmarks, and events
    """
    source = ReplaySource(replay_path)
    
    for replay_frame in source.frames:
        yield replay_frame