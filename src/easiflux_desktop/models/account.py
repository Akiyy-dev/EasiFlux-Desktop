"""Desktop account models."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass
class DesktopBalance:
    coin: str
    equity: Decimal
    wallet_balance: Decimal
    available_balance: Decimal

    @property
    def available_display(self) -> str:
        return f"{self.available_balance:.4f} {self.coin}"


@dataclass
class DesktopAccount:
    account_id: str
    label: str
    balances: list[DesktopBalance]

    @property
    def total_equity_usd(self) -> Decimal:
        return sum((b.equity for b in self.balances), Decimal("0"))
