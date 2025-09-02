"""Minimal overlay showing scroll direction and velocity."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import tkinter as tk
from tkinter import Canvas
import math
import threading

from glide.gestures.circular import CircularDirection


@dataclass
class HUDMetrics:
    """Visual metrics for HUD display."""
    window_width: int = 120
    window_height: int = 60
    opacity: float = 0.8
    fade_duration_ms: int = 500
    position: str = "bottom-right"  # bottom-right, bottom-center, etc.


class ScrollHUD:
    """Minimal overlay showing scroll direction and velocity.
    
    POC Implementation:
    - Simple tkinter window
    - Circular arrow indicator
    - Fade in/out animations
    - Thread-safe updates
    """
    
    def __init__(self, metrics: HUDMetrics):
        """Initialize HUD with display metrics."""
        self.metrics = metrics
        self._window: Optional[tk.Toplevel] = None
        self._canvas: Optional[Canvas] = None
        self._fade_timer = None
        self._current_alpha = 0.0
        self._target_alpha = 0.0
        self._lock = threading.Lock()
        
        # Try to create window
        try:
            self._create_window()
        except Exception as e:
            pass  # Failed to create HUD window
    
    def show_scroll(self, direction: CircularDirection, velocity: float) -> None:
        """
        Display scroll indicator.
        
        Args:
            direction: Scroll direction (CW/CCW)
            velocity: Normalized velocity (0.0-1.0)
        """
        if self._window is None:
            return
        
        with self._lock:
            try:
                # Update display
                self._update_display(direction, velocity)
                
                # Start fade in
                self._target_alpha = self.metrics.opacity
                self._animate_fade()
                
                # Reset fade timer
                if self._fade_timer:
                    self._window.after_cancel(self._fade_timer)
                
                # Schedule fade out
                self._fade_timer = self._window.after(
                    self.metrics.fade_duration_ms,
                    self.hide
                )
            except Exception as e:
                pass  # Error updating HUD display
    
    def hide(self) -> None:
        """Hide HUD with fade animation."""
        if self._window is None:
            return
        
        with self._lock:
            self._target_alpha = 0.0
            self._animate_fade()
    
    def _create_window(self) -> None:
        """Create transparent overlay window."""
        # Create root if needed
        self._root = tk.Tk()
        self._root.withdraw()  # Hide root window
        
        # Create toplevel window
        self._window = tk.Toplevel(self._root)
        self._window.overrideredirect(True)  # No window decorations
        self._window.attributes('-topmost', True)  # Always on top
        
        # Set transparency (platform-specific)
        try:
            self._window.attributes('-alpha', 0.0)  # Start invisible
            # macOS specific
            self._window.attributes('-transparent', True)
        except:
            pass
        
        # Configure window
        self._window.configure(bg='black')
        
        # Position window
        self._position_window()
        
        # Create canvas for drawing
        self._canvas = Canvas(
            self._window,
            width=self.metrics.window_width,
            height=self.metrics.window_height,
            bg='black',
            highlightthickness=0
        )
        self._canvas.pack()
        
        # Don't show until needed
        self._window.withdraw()
    
    def _position_window(self) -> None:
        """Position the window based on metrics."""
        if not self._window:
            return
        
        # Get screen dimensions
        screen_width = self._window.winfo_screenwidth()
        screen_height = self._window.winfo_screenheight()
        
        # Calculate position
        margin = 20
        if self.metrics.position == "bottom-right":
            x = screen_width - self.metrics.window_width - margin
            y = screen_height - self.metrics.window_height - margin
        elif self.metrics.position == "bottom-center":
            x = (screen_width - self.metrics.window_width) // 2
            y = screen_height - self.metrics.window_height - margin
        else:  # Default to bottom-right
            x = screen_width - self.metrics.window_width - margin
            y = screen_height - self.metrics.window_height - margin
        
        self._window.geometry(f"{self.metrics.window_width}x{self.metrics.window_height}+{x}+{y}")
    
    def _update_display(self, direction: CircularDirection, velocity: float) -> None:
        """Update HUD content."""
        if not self._canvas:
            return
        
        # Clear canvas
        self._canvas.delete("all")
        
        # Calculate arrow parameters
        center_x = self.metrics.window_width // 2
        center_y = self.metrics.window_height // 2
        radius = min(center_x, center_y) - 10
        
        # Draw circular arrow
        if direction == CircularDirection.CLOCKWISE:
            # Clockwise arrow (top to right)
            start_angle = 270
            extent = 90
            arrow_end = 0  # Right side
        else:
            # Counter-clockwise arrow (top to left)
            start_angle = 270
            extent = -90
            arrow_end = 180  # Left side
        
        # Draw arc
        self._canvas.create_arc(
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius,
            start=start_angle, extent=extent,
            style=tk.ARC, width=3,
            outline='white'
        )
        
        # Draw arrowhead
        arrow_angle = math.radians(arrow_end)
        arrow_x = center_x + radius * math.cos(arrow_angle)
        arrow_y = center_y + radius * math.sin(arrow_angle)
        
        # Arrowhead points
        head_size = 8
        angle1 = arrow_angle + math.radians(150)
        angle2 = arrow_angle - math.radians(150)
        
        points = [
            arrow_x, arrow_y,
            arrow_x + head_size * math.cos(angle1),
            arrow_y + head_size * math.sin(angle1),
            arrow_x + head_size * math.cos(angle2),
            arrow_y + head_size * math.sin(angle2),
        ]
        
        self._canvas.create_polygon(points, fill='white', outline='white')
        
        # Show window if hidden
        self._window.deiconify()
    
    def _animate_fade(self) -> None:
        """Animate fade in/out."""
        if not self._window:
            return
        
        # Calculate new alpha
        alpha_step = 0.1
        if self._current_alpha < self._target_alpha:
            self._current_alpha = min(self._current_alpha + alpha_step, self._target_alpha)
        elif self._current_alpha > self._target_alpha:
            self._current_alpha = max(self._current_alpha - alpha_step, self._target_alpha)
        
        # Apply alpha
        try:
            self._window.attributes('-alpha', self._current_alpha)
        except:
            pass
        
        # Continue animation if needed
        if abs(self._current_alpha - self._target_alpha) > 0.01:
            self._window.after(30, self._animate_fade)
        elif self._current_alpha == 0.0:
            # Hide window when fully transparent
            self._window.withdraw()
    
    def destroy(self) -> None:
        """Clean up resources."""
        if self._window:
            try:
                self._window.destroy()
            except:
                pass
        if hasattr(self, '_root'):
            try:
                self._root.destroy()
            except:
                pass