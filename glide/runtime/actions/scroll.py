"""Base scroll action components and dispatcher."""

from __future__ import annotations

from typing import Optional, Protocol
from dataclasses import dataclass

from glide.gestures.circular import CircularEvent, CircularDirection


@dataclass
class ScrollConfig:
    """Configuration for scroll behavior."""
    # Mapping: 180 degrees ≈ 400 pixels
    pixels_per_degree: float = 2.22  # 400/180
    
    # Smooth scrolling parameters
    max_velocity: float = 100.0  # pixels per event
    acceleration_curve: float = 1.5  # exponential factor
    
    # Natural scrolling preference
    respect_system_preference: bool = True
    
    # HUD display
    show_hud: bool = True
    hud_fade_duration_ms: int = 500


class ScrollAction(Protocol):
    """Protocol for scroll action implementations."""
    
    def execute(self, event: CircularEvent) -> None:
        """Execute scroll action based on circular event."""
        ...
    
    def cancel(self) -> None:
        """Cancel any ongoing scroll animations."""
        ...


class ScrollDispatcher:
    """Dispatches circular events to platform-specific scroll actions.
    
    POC Implementation:
    - Direct dispatch without queuing
    - Simple error logging
    - No thread safety
    """
    
    def __init__(self, config: ScrollConfig, action: Optional[ScrollAction] = None):
        """
        Initialize dispatcher with configuration.
        
        Args:
            config: Scroll behavior configuration
            action: Platform-specific scroll implementation (auto-detected if None)
        """
        self.config = config
        self.action = action
        self._hud = None
        
        # Auto-detect platform action if not provided
        if self.action is None:
            self._auto_detect_action()
        
        # Initialize HUD if enabled
        if self.config.show_hud:
            self._init_hud()
    
    def _auto_detect_action(self) -> None:
        """Auto-detect the appropriate scroll action for the platform."""
        import platform
        
        if platform.system() == "Darwin":  # macOS
            try:
                from glide.runtime.actions.quartz_scroll import QuartzScrollAction
                self.action = QuartzScrollAction(self.config)
                # Successfully initialized QuartzScrollAction
            except ImportError as e:
                # Failed to import QuartzScrollAction
                self.action = None
        else:
            # No scroll action available for this platform
            self.action = None
    
    def _init_hud(self) -> None:
        """Initialize the HUD overlay."""
        try:
            from glide.runtime.ui.scroll_hud import ScrollHUD, HUDMetrics
            
            metrics = HUDMetrics(
                fade_duration_ms=self.config.hud_fade_duration_ms,
                position="bottom-right"  # TODO: Get from config
            )
            self._hud = ScrollHUD(metrics)
            # HUD initialized successfully
        except Exception as e:
            # Failed to initialize HUD
            self._hud = None
    
    def dispatch(self, event: CircularEvent) -> bool:
        """
        Dispatch circular event to scroll action.
        
        Args:
            event: Circular gesture event to process
            
        Returns:
            True if event was handled, False otherwise
        """
        if self.action is None:
            return False
        
        try:
            # Simple POC dispatch - no validation or queuing
            self.action.execute(event)
            
            # Show HUD if enabled
            if self._hud:
                # Calculate normalized velocity (0-1)
                pixels = event.total_angle_deg * self.config.pixels_per_degree
                velocity = min(1.0, pixels / self.config.max_velocity)
                self._hud.show_scroll(event.direction, velocity)
            
            return True
        except Exception as e:
            # Error dispatching scroll event
            return False
    
    def update_config(self, config: ScrollConfig) -> None:
        """Update runtime configuration."""
        self.config = config
        # Update action's config if it has the attribute
        if hasattr(self.action, 'config'):
            self.action.config = config