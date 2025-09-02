"""Processing pipeline that orchestrates components."""

import time
from typing import Optional, List
import cv2

from glide.core.contracts import FrameSource, HandDetector, GestureDetector, EventSink
from glide.core.types import AppConfig, GateState
from glide.features.kinematics import KinematicsTracker
from glide.features.poses import check_hand_pose
from glide.gestures.touchproof import TouchProofDetector
from glide.gestures.circular import CircularDetector
from glide.ui.overlay import draw_info
from glide.runtime.actions.scroll import ScrollDispatcher, ScrollConfig


class Pipeline:
    """Main processing pipeline that connects all components."""
    
    def __init__(
        self,
        source: FrameSource,
        hand_detector: HandDetector,
        config: AppConfig,
        sink: EventSink,
        display: bool = True
    ):
        self.source = source
        self.hand_detector = hand_detector
        self.config = config
        self.sink = sink
        self.display = display
        
        # Initialize scroll dispatcher if enabled
        self.scroll_dispatcher = None
        if config.scroll.enabled:
            scroll_config = ScrollConfig(
                pixels_per_degree=config.scroll.pixels_per_degree,
                max_velocity=config.scroll.max_velocity,
                acceleration_curve=config.scroll.acceleration_curve,
                respect_system_preference=config.scroll.respect_system_preference,
                show_hud=config.scroll.show_hud,
                hud_fade_duration_ms=config.scroll.hud_fade_duration_ms,
            )
            self.scroll_dispatcher = ScrollDispatcher(scroll_config)
        
        # Initialize processors
        self.kinematics = KinematicsTracker(
            ema_alpha=config.kinematics.ema_alpha,
            buffer_frames=config.kinematics.buffer_frames
        )
        self.touchproof = TouchProofDetector(config.touchproof)
        self.circular = CircularDetector(
            min_angle_deg=config.circular.min_angle_deg,
            max_angle_deg=config.circular.max_angle_deg,
            min_speed=config.circular.min_speed,
            exit_speed_factor=config.circular.exit_speed_factor,
            max_duration_ms=config.circular.max_duration_ms,
            cooldown_ms=config.circular.cooldown_ms,
            angle_tolerance_deg=config.circular.angle_tolerance_deg,
        )
        
        # State
        self.last_event = None
        self.event_display_time = 0
        self.fps = 0.0
        self._was_touching = False
    
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
                event = self._process_frame(frame)
                
                # Emit event if detected
                if event:
                    self.sink.emit(event)
                    self.last_event = event
                    self.event_display_time = time.time()
                    
                    # Dispatch to scroll action if enabled
                    if self.scroll_dispatcher:
                        self.scroll_dispatcher.dispatch(event)
                
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
            return None
        
        # Update kinematics
        kin_state = self.kinematics.compute(detection.landmarks)
        if kin_state is None:
            return None
        
        # Check poses
        poses = check_hand_pose(detection.landmarks)
        if not (poses.open_palm or poses.pointing_index or poses.two_up):
            return None
        
        # Update touch detection
        touch_signals = self.touchproof.update(
            detection.landmarks,
            frame.image,
            frame.width,
            frame.height
        )
        
        # Track touch state changes
        self._was_touching = touch_signals.is_touching
        
        # Detect circular gestures when touching
        now_ms = int(time.time() * 1000)
        avg_finger_len = (kin_state.finger_length_idx + 
                         (kin_state.finger_length_mid or kin_state.finger_length_idx)) / 2.0
        
        circular_result = self.circular.update(
            self.kinematics.trail_mean,
            avg_finger_len,
            touch_signals.is_touching,
            now_ms
        )
        
        chosen = circular_result.event
        
        # Store detection info for display
        self._last_det = detection
        self._last_poses = poses
        self._last_touch_signals = touch_signals
        
        return chosen
    
    def _handle_display(self, frame) -> bool:
        """Handle display and user input. Returns False to quit."""
        display_frame = frame.image.copy()
        
        # Draw HUD
        draw_info(
            display_frame,
            getattr(self, '_last_det', None),
            getattr(self, '_last_poses', None),
            self.last_event if time.time() - self.event_display_time < 1.0 else None,
            None,  # gate_status not used anymore
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
        self.sink.close()
        self.source.release()
        if self.display:
            cv2.destroyAllWindows()