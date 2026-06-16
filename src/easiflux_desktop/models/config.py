"""Desktop configuration models."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum

from easiflux_desktop.core.constants import DEFAULT_BASE_URL, DEFAULT_SYMBOL, DEFAULT_WATCHLIST_SYMBOLS


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
    watchlist_symbols: list[str] = field(default_factory=lambda: list(DEFAULT_WATCHLIST_SYMBOLS))
    theme: ThemeMode = ThemeMode.DARK
    kline_interval: str = "1"
    use_websocket: bool = True
    ticker_poll_interval: float = 5.0
    window_width: int = 1400
    window_height: int = 900
    accounts: list[str] = field(default_factory=lambda: ["default"])
    risk_enabled: bool = True
    risk_max_order_qty: Decimal = Decimal("100")
    risk_max_price_deviation_pct: Decimal = Decimal("5")
    risk_max_daily_orders: int = 500
