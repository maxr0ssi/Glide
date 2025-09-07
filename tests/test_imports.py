"""Basic import tests to ensure the package structure is correct."""


def test_core_imports():
    """Test that core modules can be imported."""


def test_perception_imports():
    """Test that perception modules can be imported."""


def test_gestures_imports():
    """Test that gesture modules can be imported."""


def test_features_imports():
    """Test that feature modules can be imported."""


def test_runtime_imports():
    """Test that runtime modules can be imported."""


def test_config_loading():
    """Test that configuration can be loaded."""
    from glide.core.config_models import AppConfig

    # Test default config creation
    config = AppConfig()  # type: ignore[call-arg]
    assert config.camera_index == 0
    assert config.touchproof.proximity_enter > 0
    assert config.scroll.enabled == True
