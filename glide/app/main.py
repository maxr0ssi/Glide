"""Main entry point for Glide gesture control."""

from __future__ import annotations

import argparse
import time
import cv2  # type: ignore

from glide.core.types import AppConfig
from glide.perception.camera import Camera
from glide.perception.hands import HandLandmarker
from glide.features.poses import check_hand_pose
from glide.features.kinematics import KinematicsTracker
from glide.gestures.touchproof import TouchProofDetector
from glide.gestures.velocity_tracker import VelocityTracker
from glide.gestures.velocity_controller import VelocityController
from glide.ui.overlay import draw_info
from glide.runtime.actions.config import ScrollConfig
from glide.runtime.actions.velocity_dispatcher import VelocityScrollDispatcher


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Glide - Gesture Detection")
    p.add_argument("--config", type=str, default="glide/io/defaults.yaml")
    p.add_argument("--debug", action="store_true")
    p.add_argument("--model", type=str, default="models/hand_landmarker.task", help="Path to MediaPipe hand_landmarker.task")
    p.add_argument("--headless", action="store_true", help="Run without preview window")
    p.add_argument("--no-hud", action="store_true", help="Disable scroll HUD overlay")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    config = AppConfig.from_yaml(args.config)

    camera = Camera(index=config.camera_index, width=config.frame_width, mirror=config.mirror)
    hands = HandLandmarker(model_path=args.model)
    kinematics = KinematicsTracker(ema_alpha=config.kinematics.ema_alpha, buffer_frames=config.kinematics.buffer_frames)
    touchproof = TouchProofDetector(config.touchproof)
    
    # Initialize velocity-based scrolling components
    velocity_tracker = VelocityTracker()
    velocity_controller = VelocityController()
    
    # Initialize scroll dispatcher if enabled
    scroll_dispatcher = None
    if config.scroll.enabled:
        scroll_config = ScrollConfig(
            pixels_per_degree=config.scroll.pixels_per_degree,
            max_velocity=config.scroll.max_velocity,
            acceleration_curve=config.scroll.acceleration_curve,
            respect_system_preference=config.scroll.respect_system_preference,
            show_hud=config.scroll.show_hud and not args.no_hud and not args.headless,  # Disable HUD in headless mode
            hud_fade_duration_ms=config.scroll.hud_fade_duration_ms,
        )
        scroll_dispatcher = VelocityScrollDispatcher(scroll_config)

    # FPS tracking
    fps = 0.0
    last_time = time.time()
    frame_count = 0
    
    # Event display timer
    last_event = None
    event_display_time = 0
    
    try:
        while True:
            # frame_start = time.time()
            
            frame = camera.read()
            if frame is None:
                break
                
            # Make a copy for display
            display_frame = frame.image.copy() if not args.headless else None
            
            detection = hands.detect(frame.image)
            
            # Initialize poses to None
            poses = None
            # is_touching = False
            touch_signals = None
            
            if detection is None or detection.confidence < config.gates.presence_conf:
                # Draw info even when no hand detected
                if display_frame is not None:
                    draw_info(display_frame, None, None,
                              fps, config.touch_threshold_pixels, None)
            else:
                # ROI/palm-relative alignment and fingertip kinematics
                kin_state = kinematics.compute(detection.landmarks)
                
                # Pose gate
                poses = check_hand_pose(detection.landmarks)
                
                # TouchProof multi-signal detection
                touch_signals = touchproof.update(
                    detection.landmarks,
                    frame.image,
                    frame.width,
                    frame.height
                )
                
                # Track touch state changes
                if not hasattr(main, '_was_touching'):
                    main._was_touching = False
                main._was_touching = touch_signals.is_touching
                
                if kin_state is not None and (poses.open_palm or poses.pointing_index or poses.two_up):
                    # Get current time and finger length
                    now_ms = int(time.time() * 1000)
                    avg_finger_len = (kin_state.finger_length_idx + 
                                    (kin_state.finger_length_mid or kin_state.finger_length_idx)) / 2.0
                    
                    # Update smooth scrolling if enabled
                    scroll_update = None
                    if config.scroll.enabled and scroll_dispatcher:
                        # Get fingertip positions (index=8, middle=12 in MediaPipe)
                        index_tip = detection.landmarks[8]
                        middle_tip = detection.landmarks[12]
                        
                        # Update velocity tracker
                        velocity = velocity_tracker.update(
                            (index_tip.x, index_tip.y),
                            (middle_tip.x, middle_tip.y),
                            touch_signals.is_touching,
                            now_ms
                        )
                        
                        # Check for single finger (only index extended)
                        is_single_finger = poses.pointing_index and not poses.two_up
                        
                        # Update wheel controller
                        # High-five: open palm + not touching + not in two-finger or pointing pose
                        is_high_five = (
                            poses.open_palm and not touch_signals.is_touching and not (poses.two_up or poses.pointing_index)
                        )
                        scroll_update = velocity_controller.update(
                            velocity,
                            touch_signals.is_touching,
                            is_high_five,
                            now_ms
                        )
                        
                        # Debug logging (disabled for production)
                        # if velocity:
                        #     print(f"[DEBUG] vel=({velocity.x:.3f}, {velocity.y:.3f}), mag={velocity.magnitude:.3f}, touching={touch_signals.is_touching}, state={scroll_update.state.value}, active={scroll_update.is_active}")
                        
                        # Dispatch continuous scrolling
                        if scroll_update:
                            scroll_dispatcher.dispatch(
                                scroll_update.velocity,
                                scroll_update.state,
                                scroll_update.is_active
                            )
                    
                
                # Draw info with detection
                if display_frame is not None:
                    draw_info(display_frame, detection, poses,
                             fps, config.touch_threshold_pixels, touch_signals)
            
            # Show preview window
            if not args.headless and display_frame is not None:
                cv2.imshow('Glide - Gesture Detection', display_frame)
                
                # Check for quit
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:  # 'q' or ESC
                    break
            elif args.headless:
                # In headless mode, add small delay to maintain reasonable frame rate
                time.sleep(0.001)  # 1ms delay, similar to cv2.waitKey(1)
            
            # Update FPS
            frame_count += 1
            current_time = time.time()
            if current_time - last_time >= 1.0:
                fps = frame_count / (current_time - last_time)
                frame_count = 0
                last_time = current_time

    except KeyboardInterrupt:
        pass
    finally:
        camera.release()
        if not args.headless:
            cv2.destroyAllWindows()


if __name__ == "__main__":
    main()