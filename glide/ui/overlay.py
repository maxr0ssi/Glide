"""Display and visualization functions for Glide."""

import cv2
import numpy as np
import time
from typing import Optional
from glide.core.types import HandDet, PoseFlags
from glide.gestures.touchproof import TouchProofSignals
from glide.ui.utils import get_pixel_distance


def draw_info(
    image: np.ndarray, 
    det: Optional[HandDet], 
    poses: Optional[PoseFlags], 
    fps: float = 0.0, 
    touch_threshold: float = 20.0, 
    touch_signals: Optional[TouchProofSignals] = None
) -> None:
    """Draw detection info on preview image"""
    height, width = image.shape[:2]
    
    # FPS (top left)
    cv2.putText(image, f"FPS: {fps:.1f}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    # TouchProof signals - Clean table on right side
    if touch_signals is not None:
        # Large status circle on left
        circle_x = 60
        circle_y = height // 2
        circle_radius = 40
        touch_color = (0, 255, 0) if touch_signals.is_touching else (0, 0, 255)
        cv2.circle(image, (circle_x, circle_y), circle_radius, touch_color, -1)
        cv2.circle(image, (circle_x, circle_y), circle_radius + 2, (255, 255, 255), 2)  # White border
        
        # Table on right side (expanded for new signals)
        table_x = width - 240
        table_y = 60
        table_width = 220
        table_height = 350
        
        # Semi-transparent background
        overlay = image.copy()
        cv2.rectangle(overlay, (table_x, table_y), (table_x + table_width, table_y + table_height), 
                     (40, 40, 40), -1)
        cv2.addWeighted(overlay, 0.7, image, 0.3, 0, image)
        
        # Table border
        cv2.rectangle(image, (table_x, table_y), (table_x + table_width, table_y + table_height), 
                     (200, 200, 200), 1)
        
        # Title
        title_y = table_y + 25
        cv2.putText(image, "Touch Signals", (table_x + 10, title_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Divider line
        cv2.line(image, (table_x + 10, title_y + 5), (table_x + table_width - 10, title_y + 5), 
                (200, 200, 200), 1)
        
        # Signal rows
        signals = [
            ("Distance:", 1.0 - touch_signals.distance_factor),  # Invert for display
            ("", None),  # Spacer
            ("Proximity:", touch_signals.proximity_score),
            ("Angle:", touch_signals.angle_score),
            ("MFC:", touch_signals.mfc_score),
            ("", None),  # Spacer
            ("Fused Score:", touch_signals.fused_score)
        ]
        
        row_y = title_y + 30
        for label, value in signals:
            if value is not None:
                # Label
                cv2.putText(image, label, (table_x + 15, row_y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
                
                # Value with color coding
                value_color = (0, 255, 0) if value > 0.7 else (0, 255, 255) if value > 0.4 else (0, 100, 255)
                
                # Add asterisk for conditionally computed signals
                value_text = f"{value:.2f}"
                if label in ["SVT:", "MFC:"] and 0.45 <= touch_signals.fused_score <= 0.65:
                    value_text += "*"  # Indicate active computation
                
                cv2.putText(image, value_text, (table_x + 130, row_y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, value_color, 2)
                
                # Mini bar
                bar_x = table_x + 15
                bar_y = row_y + 5
                bar_width = int(100 * value)
                cv2.rectangle(image, (bar_x, bar_y), (bar_x + bar_width, bar_y + 3), 
                            value_color, -1)
                cv2.rectangle(image, (bar_x, bar_y), (bar_x + 100, bar_y + 3), 
                            (100, 100, 100), 1)
            
            row_y += 30 if label else 15  # Smaller spacing for empty rows
        
        # Add distance indicator at bottom
        dist_y = table_y + table_height - 30
        cv2.putText(image, "Hand Distance", (table_x + 10, dist_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
        
        # Distance bar
        bar_x = table_x + 10
        bar_y = dist_y + 10
        bar_width = 200
        bar_height = 8
        
        # Background
        cv2.rectangle(image, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height),
                     (50, 50, 50), -1)
        
        # Distance indicator (inverse of distance_factor)
        dist_pixels = int((1.0 - touch_signals.distance_factor) * bar_width)
        dist_color = (0, 255, 0) if touch_signals.distance_factor < 0.3 else \
                     (0, 255, 255) if touch_signals.distance_factor < 0.7 else (0, 100, 255)
        cv2.rectangle(image, (bar_x, bar_y), (bar_x + dist_pixels, bar_y + bar_height),
                     dist_color, -1)
        
        # Labels
        cv2.putText(image, "Far", (bar_x, bar_y - 3),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.3, (150, 150, 150), 1)
        cv2.putText(image, "Close", (bar_x + bar_width - 25, bar_y - 3),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.3, (150, 150, 150), 1)
    
    # Hand detection status
    if det is not None:
        status = f"Hand: Detected (conf: {det.confidence:.2f})"
        cv2.putText(image, status, (10, height - 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Pose status
        if poses is not None:
            pose_text = "Poses: "
            if poses.open_palm:
                pose_text += "Open Palm "
            if poses.pointing_index:
                pose_text += "Pointing "
            if poses.two_up:
                pose_text += "Two Up "
            cv2.putText(image, pose_text, (10, height - 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        # Draw hand landmarks
        h, w = image.shape[:2]
        
        # Get fingertip info for backward compatibility
        distance, (idx_x, idx_y), (mid_x, mid_y) = get_pixel_distance(det.landmarks, w, h)
        
        # Draw all landmarks in small size
        for i, landmark in enumerate(det.landmarks):
            x = int(landmark.x * w)
            y = int(landmark.y * h)
            if i == 8 or i == 12:  # Skip fingertips, we'll draw them specially
                continue
            cv2.circle(image, (x, y), 2, (0, 255, 0), -1)
        
        # Draw fingertips with special highlighting
        is_touching = touch_signals.is_touching if touch_signals else False
        tip_color = (0, 255, 0) if is_touching else (0, 0, 255)
        cv2.circle(image, (idx_x, idx_y), 8, tip_color, -1)  # Index tip
        cv2.circle(image, (mid_x, mid_y), 8, tip_color, -1)  # Middle tip
        
        # Draw line between fingertips
        cv2.line(image, (idx_x, idx_y), (mid_x, mid_y), tip_color, 2)
        
        # Show distance and touch status
        touch_text = "TOUCHING" if is_touching else "NOT TOUCHING"
        touch_color = (0, 255, 0) if is_touching else (0, 0, 255)
        cv2.putText(image, touch_text, (width // 2 - 80, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, touch_color, 3)
        
        cv2.putText(image, f"Distance: {distance:.1f} px", (width // 2 - 80, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Show threshold
        cv2.putText(image, f"Threshold: {touch_threshold:.0f} px", (width // 2 - 80, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    else:
        cv2.putText(image, "Hand: Not detected", (10, height - 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
