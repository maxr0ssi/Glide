"""Configuration loading with defaults, YAML, and CLI merging."""

from pathlib import Path
from typing import Optional, Dict, Any
import yaml

from glide.core.types import AppConfig


def load_config(
    yaml_path: Optional[str] = None,
    cli_overrides: Optional[Dict[str, Any]] = None
) -> AppConfig:
    """Load configuration with merge order: defaults < YAML < CLI.
    
    Args:
        yaml_path: Optional path to YAML config file
        cli_overrides: Optional dict of CLI overrides
        
    Returns:
        Merged AppConfig instance
    """
    # Start with defaults
    config = AppConfig()
    
    # Load from YAML if provided
    if yaml_path:
        config = AppConfig.from_yaml(yaml_path)
    
    # Apply CLI overrides
    if cli_overrides:
        _apply_overrides(config, cli_overrides)
    
    return config


def _apply_overrides(config: AppConfig, overrides: Dict[str, Any]) -> None:
    """Apply CLI overrides to config object.
    
    Supports nested keys with dots, e.g., 'touchproof.proximity_enter'
    """
    for key, value in overrides.items():
        if '.' in key:
            # Handle nested keys
            parts = key.split('.')
            obj = config
            for part in parts[:-1]:
                obj = getattr(obj, part)
            setattr(obj, parts[-1], value)
        else:
            # Top-level key
            if hasattr(config, key):
                setattr(config, key, value)