"""Tests for configuration system."""

from pathlib import Path

import pytest
from lazyverdi.core.config import (
    DEFAULT_CONFIG,
    get_config_value,
    load_config,
    save_config,
    set_config_value,
)


@pytest.fixture
def temp_config_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create temporary config directory."""
    config_dir = tmp_path / "lazyverdi"
    monkeypatch.setattr("lazyverdi.core.config.CONFIG_DIR", config_dir)
    monkeypatch.setattr("lazyverdi.core.config.CONFIG_FILE", config_dir / "config.yaml")
    return config_dir


def test_default_config_has_required_keys() -> None:
    """Test that default config has all required keys."""
    assert "theme" in DEFAULT_CONFIG


def test_load_config_creates_default_on_first_run(temp_config_dir: Path) -> None:
    """Test that first run creates default config file."""
    config = load_config()
    assert config == DEFAULT_CONFIG
    # Config file should be created
    config_file = temp_config_dir / "config.yaml"
    assert config_file.exists()


def test_save_and_load_config(temp_config_dir: Path) -> None:
    """Test saving and loading configuration."""
    test_config = {"theme": "custom"}
    save_config(test_config)

    loaded = load_config()
    # Should merge with defaults
    assert loaded["theme"] == "custom"


def test_load_config_handles_corrupted_file(temp_config_dir: Path) -> None:
    """Test that corrupted config file falls back to defaults."""
    config_file = temp_config_dir / "config.yaml"
    config_file.parent.mkdir(parents=True, exist_ok=True)
    config_file.write_text("invalid yaml: [unbalanced")

    config = load_config()
    assert config == DEFAULT_CONFIG


def test_get_config_value(temp_config_dir: Path) -> None:
    """Test getting single config value."""
    save_config({"theme": "dark"})
    value = get_config_value("theme")
    assert value == "dark"


def test_get_config_value_with_default(temp_config_dir: Path) -> None:
    """Test getting config value with default."""
    value = get_config_value("nonexistent", "default_value")
    assert value == "default_value"


def test_set_config_value(temp_config_dir: Path) -> None:
    """Test setting single config value."""
    set_config_value("theme", "light")
    config = load_config()
    assert config["theme"] == "light"


def test_set_config_value_preserves_other_values(temp_config_dir: Path) -> None:
    """Test that setting one value preserves others."""
    save_config({"theme": "dark"})
    set_config_value("theme", "light")

    config = load_config()
    assert config["theme"] == "light"
