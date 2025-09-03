"""Processing pipeline that orchestrates components."""

import time
import cv2

from glide.core.contracts import FrameSource, HandDetector
from glide.core.types import AppConfig
from glide.features.kinematics import KinematicsTracker
from glide.features.poses import check_hand_pose
from glide.gestures.touchproof import TouchProofDetector
from glide.ui.overlay import draw_info


class Pipeline:
    """Main processing pipeline that connects all components."""
    
    def __init__(
        self,
        source: FrameSource,
        hand_detector: HandDetector,
        config: AppConfig,
        display: bool = True
    ):
        self.source = source
        self.hand_detector = hand_detector
        self.config = config
        self.display = display
        
        
        # Initialize processors
        self.kinematics = KinematicsTracker(
            ema_alpha=config.kinematics.ema_alpha,
            buffer_frames=config.kinematics.buffer_frames
        )
        self.touchproof = TouchProofDetector(config.touchproof)
        
        
        # State
        self.fps = 0.0
    
    def run(self) -> None:
        """Run the main processing loop."""
        # FPS tracking
        last_time = time.time()
        frame_count = 0
        
        try:
            while True:
                # Read frame
                frame = self.source.read()
                if frame is None:
                    break
                
                # Process frame
                self._process_frame(frame)
                
                # Update FPS
                frame_count += 1
                current_time = time.time()
                if current_time - last_time >= 1.0:
                    self.fps = frame_count / (current_time - last_time)
                    frame_count = 0
                    last_time = current_time
                
                # Display
                if self.display and not self._handle_display(frame):
                    break
                    
        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()
    
    def _process_frame(self, frame):
        """Process a single frame through the detection pipeline."""
        # Detect hands
        detection = self.hand_detector.detect(frame.image)
        
        if detection is None or detection.confidence < self.config.gates.presence_conf:
            self._last_det = None
            self._last_poses = None
            self._last_touch_signals = None
            return
        
        # Update kinematics
        kin_state = self.kinematics.compute(detection.landmarks)
        if kin_state is None:
            return
        
        # Check poses
        poses = check_hand_pose(detection.landmarks)
        if not (poses.open_palm or poses.pointing_index or poses.two_up):
            return
        
        # Update touch detection
        touch_signals = self.touchproof.update(
            detection.landmarks,
            frame.image,
            frame.width,
            frame.height
        )
        
        # Store detection info for display
        self._last_det = detection
        self._last_poses = poses
        self._last_touch_signals = touch_signals
    
    def _handle_display(self, frame) -> bool:
        """Handle display and user input. Returns False to quit."""
        display_frame = frame.image.copy()
        
        # Draw HUD
        draw_info(
            display_frame,
            getattr(self, '_last_det', None),
            getattr(self, '_last_poses', None),
            self.fps,
            self.config.touch_threshold_pixels,
            getattr(self, '_last_touch_signals', None)
        )
        
        # Show window
        cv2.imshow('Glide - Gesture Detection', display_frame)
        
        # Check for quit
        key = cv2.waitKey(1) & 0xFF
        return key not in [ord('q'), 27]  # q or ESC
    
    def cleanup(self) -> None:
        """Clean up resources."""
        self.source.release()
        if self.display:
            cv2.destroyAllWindows()