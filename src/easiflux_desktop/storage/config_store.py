"""TOML configuration persistence."""

from __future__ import annotations

from pathlib import Path

import tomllib
from platformdirs import user_config_dir

from easiflux_desktop.core.constants import APP_NAME, APP_ORG, CONFIG_FILENAME
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
            theme=ThemeMode(data.get("theme", "dark")),
            kline_interval=data.get("kline_interval", "1"),
            use_websocket=data.get("use_websocket", True),
            ticker_poll_interval=float(data.get("ticker_poll_interval", 5.0)),
            window_width=int(data.get("window_width", 1400)),
            window_height=int(data.get("window_height", 900)),
            accounts=list(data.get("accounts", ["default"])),
        )

    def save(self, config: AppConfig) -> None:
        lines = [
            f'active_symbol = "{config.active_symbol}"',
            f'active_account_id = "{config.active_account_id}"',
            f'theme = "{config.theme.value}"',
            f'kline_interval = "{config.kline_interval}"',
            f"use_websocket = {'true' if config.use_websocket else 'false'}",
            f"ticker_poll_interval = {config.ticker_poll_interval}",
            f"window_width = {config.window_width}",
            f"window_height = {config.window_height}",
            f"accounts = {config.accounts!r}",
        ]
        self._path.write_text("\n".join(lines) + "\n", encoding="utf-8")
