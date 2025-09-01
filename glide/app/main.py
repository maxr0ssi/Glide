"""Main entry point for Glide gesture control."""

from __future__ import annotations

import argparse
import time
from typing import Optional  # noqa: F401
import cv2  # type: ignore

from glide.core.types import AppConfig, GateState
from glide.perception.camera import Camera
from glide.perception.hands import HandLandmarker
from glide.features.poses import check_hand_pose
from glide.features.kinematics import KinematicsTracker
from glide.gestures.touchproof import TouchProofDetector
from glide.gestures.circular import CircularDetector
from glide.ui.overlay import draw_info
from glide.io.event_output import JsonSink, RingBufferLogger


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Glide - Gesture Detection")
    p.add_argument("--config", type=str, default="glide/io/defaults.yaml")
    p.add_argument("--debug", action="store_true")
    p.add_argument("--record", type=str, default=None, help="Path to write JSONL events")
    p.add_argument("--replay", type=str, default=None, help="Path to read replay (NYI)")
    p.add_argument("--model", type=str, default="models/hand_landmarker.task", help="Path to MediaPipe hand_landmarker.task")
    p.add_argument("--headless", action="store_true", help="Run without preview window")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    config = AppConfig.from_yaml(args.config)

    camera = Camera(index=config.camera_index, width=config.frame_width, mirror=config.mirror)
    hands = HandLandmarker(model_path=args.model)
    kinematics = KinematicsTracker(ema_alpha=config.kinematics.ema_alpha, buffer_frames=config.kinematics.buffer_frames)
    touchproof = TouchProofDetector(config.touchproof)
    circular = CircularDetector(
        min_angle_deg=config.circular.min_angle_deg,
        max_angle_deg=config.circular.max_angle_deg,
        min_speed=config.circular.min_speed,
        exit_speed_factor=config.circular.exit_speed_factor,
        max_duration_ms=config.circular.max_duration_ms,
        cooldown_ms=config.circular.cooldown_ms,
        angle_tolerance_deg=config.circular.angle_tolerance_deg,
    )
    sink = JsonSink(args.record)
    ring = RingBufferLogger()

    # FPS tracking
    fps = 0.0
    last_time = time.time()
    frame_count = 0
    
    # Event display timer
    last_event = None
    event_display_time = 0
    
    try:
        while True:
            frame_start = time.time()
            
            frame = camera.read()
            if frame is None:
                break
                
            # Make a copy for display
            display_frame = frame.image.copy() if not args.headless else None
            
            detection = hands.detect(frame.image)
            
            # Initialize poses and gate_status to None
            poses = None
            gate_status = None
            is_touching = False
            touch_signals = None
            
            if detection is None or detection.confidence < config.gates.presence_conf:
                # Draw info even when no hand detected
                if display_frame is not None:
                    draw_info(display_frame, None, None, 
                             last_event if time.time() - event_display_time < 1.0 else None, None, fps, 
                             config.touch_threshold_pixels, None)
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
                    # Detect circular gestures when touching
                    now_ms = int(time.time() * 1000)
                    avg_finger_len = (kin_state.finger_length_idx + 
                                    (kin_state.finger_length_mid or kin_state.finger_length_idx)) / 2.0
                    
                    circular_result = circular.update(
                        kinematics.trail_mean,
                        avg_finger_len,
                        touch_signals.is_touching,
                        now_ms
                    )
                    
                    if circular_result.event is not None:
                        sink.emit(circular_result.event)
                        ring.append(circular_result.event)
                        last_event = circular_result.event
                        event_display_time = time.time()
                
                # Draw info with detection
                if display_frame is not None:
                    draw_info(display_frame, detection, poses,
                             last_event if time.time() - event_display_time < 1.0 else None, 
                             gate_status, fps, config.touch_threshold_pixels, touch_signals)
            
            # Show preview window
            if not args.headless and display_frame is not None:
                cv2.imshow('Glide - Gesture Detection', display_frame)
                
                # Check for quit
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:  # 'q' or ESC
                    break
            
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
        sink.close()
        camera.release()
        if not args.headless:
            cv2.destroyAllWindows()


if __name__ == "__main__":
    main()