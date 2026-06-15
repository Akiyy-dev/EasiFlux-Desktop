"""Unit tests for config store."""

from pathlib import Path

from easiflux_desktop.models.config import ThemeMode
from easiflux_desktop.storage.config_store import ConfigStore


def test_config_roundtrip(tmp_path: Path):
    store = ConfigStore(path=tmp_path / "config.toml")
    from easiflux_desktop.models.config import AppConfig

    config = AppConfig(active_symbol="ETHUSDT", theme=ThemeMode.LIGHT)
    store.save(config)
    loaded = store.load()
    assert loaded.active_symbol == "ETHUSDT"
    assert loaded.theme == ThemeMode.LIGHT
