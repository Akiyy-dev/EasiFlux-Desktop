"""Application command objects dispatched by the command bus."""

from __future__ import annotations

from dataclasses import dataclass

from easiflux_desktop.models.config import ApiCredential
from easiflux_desktop.models.trading import PlaceOrderRequest


@dataclass(frozen=True)
class ConnectCommand:
    credential: ApiCredential | None = None
    start_realtime: bool = True


@dataclass(frozen=True)
class TestConnectionCommand:
    credential: ApiCredential | None = None


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
class SetActiveSymbolCommand:
    symbol: str
