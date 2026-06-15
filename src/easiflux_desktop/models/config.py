"""Desktop configuration models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from easiflux_desktop.core.constants import DEFAULT_BASE_URL, DEFAULT_SYMBOL


class ThemeMode(str, Enum):
    DARK = "dark"
    LIGHT = "light"


class ConnectionStatus(str, Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class ApiCredential:
    api_key: str = ""
    api_secret: str = ""
    base_url: str = DEFAULT_BASE_URL
    label: str = "default"


@dataclass
class AppConfig:
    active_symbol: str = DEFAULT_SYMBOL
    active_account_id: str = "default"
    theme: ThemeMode = ThemeMode.DARK
    kline_interval: str = "1"
    use_websocket: bool = True
    ticker_poll_interval: float = 5.0
    window_width: int = 1400
    window_height: int = 900
    accounts: list[str] = field(default_factory=lambda: ["default"])
