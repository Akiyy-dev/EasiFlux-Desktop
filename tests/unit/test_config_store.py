"""Unit tests for config store."""

from decimal import Decimal
from pathlib import Path

from easiflux_desktop.models.config import ThemeMode
from easiflux_desktop.storage.config_store import ConfigStore


def test_config_roundtrip(tmp_path: Path):
    store = ConfigStore(path=tmp_path / "config.toml")
    from easiflux_desktop.models.config import AppConfig

    config = AppConfig(active_symbol="ETHUSDT", watchlist_symbols=["ETHUSDT", "BTCUSDT"], theme=ThemeMode.LIGHT)
    store.save(config)
    loaded = store.load()
    assert loaded.active_symbol == "ETHUSDT"
    assert loaded.watchlist_symbols == ["ETHUSDT", "BTCUSDT"]
    assert loaded.theme == ThemeMode.LIGHT


def test_risk_config_roundtrip(tmp_path: Path):
    store = ConfigStore(path=tmp_path / "config.toml")
    from easiflux_desktop.models.config import AppConfig

    config = AppConfig(
        risk_enabled=False,
        risk_max_order_qty=Decimal("1.5"),
        risk_max_price_deviation_pct=Decimal("2.25"),
        risk_max_daily_orders=12,
    )
    store.save(config)
    loaded = store.load()

    assert not loaded.risk_enabled
    assert loaded.risk_max_order_qty == Decimal("1.5")
    assert loaded.risk_max_price_deviation_pct == Decimal("2.25")
    assert loaded.risk_max_daily_orders == 12
