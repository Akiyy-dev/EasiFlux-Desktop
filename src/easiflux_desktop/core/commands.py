"""Application command objects dispatched by the command bus."""

from __future__ import annotations

from dataclasses import dataclass

from easiflux_desktop.models.config import ApiCredential
from easiflux_desktop.models.trading import PlaceOrderRequest
from easiflux_desktop.services.risk_manager import RiskConfig


@dataclass(frozen=True)
class ConnectCommand:
    credential: ApiCredential | None = None
    start_realtime: bool = True


@dataclass(frozen=True)
class TestConnectionCommand:
    __test__ = False

    credential: ApiCredential | None = None


@dataclass(frozen=True)
class SaveConnectionSettingsCommand:
    active_symbol: str
    use_websocket: bool
    credential: ApiCredential | None = None
    account_id: str | None = None


@dataclass(frozen=True)
class PlaceOrderCommand:
    request: PlaceOrderRequest


@dataclass(frozen=True)
class CancelOrderCommand:
    symbol: str
    order_id: str


@dataclass(frozen=True)
class RefreshOrdersCommand:
    symbol: str | None = None


@dataclass(frozen=True)
class RefreshAccountCommand:
    symbol: str | None = None


@dataclass(frozen=True)
class LoadKlinesCommand:
    symbol: str | None = None
    interval: str | None = None


@dataclass(frozen=True)
class RefreshMarketCommand:
    symbol: str | None = None


@dataclass(frozen=True)
class SetActiveSymbolCommand:
    symbol: str
    refresh: bool = True


@dataclass(frozen=True)
class SetKlineIntervalCommand:
    interval: str


@dataclass(frozen=True)
class UpdateRiskConfigCommand:
    config: RiskConfig


@dataclass(frozen=True)
class ToggleStrategyCommand:
    name: str
    enabled: bool


@dataclass(frozen=True)
class ExportAnalyticsCommand:
    filename: str = "orders_export.csv"
