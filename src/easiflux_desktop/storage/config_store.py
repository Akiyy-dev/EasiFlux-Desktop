"""TOML configuration persistence."""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

from platformdirs import user_config_dir

from easiflux_desktop.core.constants import APP_NAME, APP_ORG, CONFIG_FILENAME, DEFAULT_WATCHLIST_SYMBOLS
from easiflux_desktop.models.config import AppConfig, ThemeMode


class ConfigStore:
    def __init__(self, path: Path | None = None) -> None:
        self._path = path or Path(user_config_dir(APP_NAME, APP_ORG)) / CONFIG_FILENAME
        self._path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> AppConfig:
        if not self._path.exists():
            return AppConfig()

        data = tomllib.loads(self._path.read_text(encoding="utf-8"))
        return AppConfig(
            active_symbol=data.get("active_symbol", "BTCUSDT"),
            active_account_id=data.get("active_account_id", "default"),
            watchlist_symbols=list(data.get("watchlist_symbols", DEFAULT_WATCHLIST_SYMBOLS)),
            theme=ThemeMode(data.get("theme", "dark")),
            kline_interval=data.get("kline_interval", "1"),
            use_websocket=data.get("use_websocket", True),
            ticker_poll_interval=float(data.get("ticker_poll_interval", 5.0)),
            window_width=int(data.get("window_width", 1400)),
            window_height=int(data.get("window_height", 900)),
            accounts=list(data.get("accounts", ["default"])),
            risk_enabled=bool(data.get("risk_enabled", True)),
            risk_max_order_qty=Decimal(str(data.get("risk_max_order_qty", "100"))),
            risk_max_price_deviation_pct=Decimal(str(data.get("risk_max_price_deviation_pct", "5"))),
            risk_max_daily_orders=int(data.get("risk_max_daily_orders", 500)),
        )

    def save(self, config: AppConfig) -> None:
        lines = [
            f'active_symbol = "{config.active_symbol}"',
            f'active_account_id = "{config.active_account_id}"',
            f"watchlist_symbols = {config.watchlist_symbols!r}",
            f'theme = "{config.theme.value}"',
            f'kline_interval = "{config.kline_interval}"',
            f"use_websocket = {'true' if config.use_websocket else 'false'}",
            f"ticker_poll_interval = {config.ticker_poll_interval}",
            f"window_width = {config.window_width}",
            f"window_height = {config.window_height}",
            f"accounts = {config.accounts!r}",
            f"risk_enabled = {'true' if config.risk_enabled else 'false'}",
            f'risk_max_order_qty = "{config.risk_max_order_qty}"',
            f'risk_max_price_deviation_pct = "{config.risk_max_price_deviation_pct}"',
            f"risk_max_daily_orders = {config.risk_max_daily_orders}",
        ]
        self._path.write_text("\n".join(lines) + "\n", encoding="utf-8")
