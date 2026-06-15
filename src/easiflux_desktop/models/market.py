"""Desktop market data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal


def _to_decimal(value: object | None) -> Decimal:
    if value is None:
        return Decimal("0")
    return Decimal(str(value))


@dataclass
class DesktopTicker:
    symbol: str
    last_price: Decimal
    bid_price: Decimal
    ask_price: Decimal
    volume_24h: Decimal = Decimal("0")
    change_24h: Decimal = Decimal("0")
    change_pct: Decimal = Decimal("0")
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def spread(self) -> Decimal:
        return self.ask_price - self.bid_price

    @property
    def volume_display(self) -> str:
        vol = float(self.volume_24h)
        if vol >= 1_000_000:
            return f"{vol / 1_000_000:.2f}M"
        if vol >= 1_000:
            return f"{vol / 1_000:.2f}K"
        return f"{vol:.4f}"


@dataclass
class DesktopKline:
    symbol: str
    interval: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    timestamp: datetime


@dataclass
class DepthLevel:
    price: Decimal
    size: Decimal


@dataclass
class DesktopDepth:
    symbol: str
    bids: list[DepthLevel]
    asks: list[DepthLevel]
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
