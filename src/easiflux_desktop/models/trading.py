"""Desktop trading models."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class OrderStatus(str, Enum):
    NEW = "New"
    PARTIALLY_FILLED = "PartiallyFilled"
    FILLED = "Filled"
    CANCELLED = "Cancelled"
    REJECTED = "Rejected"
    UNKNOWN = "Unknown"

    @classmethod
    def from_raw(cls, value: str | None) -> OrderStatus:
        if not value:
            return cls.UNKNOWN
        for member in cls:
            if member.value.lower() == value.lower():
                return member
        return cls.UNKNOWN

    @property
    def display(self) -> str:
        labels = {
            OrderStatus.NEW: "新建",
            OrderStatus.PARTIALLY_FILLED: "部分成交",
            OrderStatus.FILLED: "已成交",
            OrderStatus.CANCELLED: "已撤销",
            OrderStatus.REJECTED: "已拒绝",
            OrderStatus.UNKNOWN: "未知",
        }
        return labels.get(self, value if (value := self.value) else "未知")


class PositionSide(str, Enum):
    LONG = "Buy"
    SHORT = "Sell"
    NONE = "None"

    @classmethod
    def from_raw(cls, value: str | None) -> PositionSide:
        if not value:
            return cls.NONE
        for member in cls:
            if member.value.lower() == value.lower():
                return member
        return cls.NONE


@dataclass
class DesktopOrder:
    order_id: str
    symbol: str
    side: str
    order_type: str
    price: Decimal
    qty: Decimal
    status: OrderStatus
    order_link_id: str | None = None
    filled_qty: Decimal = Decimal("0")
    avg_price: Decimal = Decimal("0")

    @property
    def status_display(self) -> str:
        return self.status.display

    @property
    def side_color(self) -> str:
        return "#26a69a" if self.side.lower() in ("buy", "long") else "#ef5350"

    @property
    def is_terminal(self) -> bool:
        return self.status in (OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED)


@dataclass
class DesktopPosition:
    symbol: str
    side: PositionSide
    size: Decimal
    entry_price: Decimal
    leverage: Decimal
    unrealised_pnl: Decimal

    @property
    def size_display(self) -> str:
        return f"{self.size}"

    @property
    def pnl_pct(self) -> Decimal:
        if self.entry_price == 0 or self.size == 0:
            return Decimal("0")
        notional = self.entry_price * abs(self.size)
        if notional == 0:
            return Decimal("0")
        return (self.unrealised_pnl / notional) * 100

    @property
    def pnl_color(self) -> str:
        if self.unrealised_pnl > 0:
            return "#26a69a"
        if self.unrealised_pnl < 0:
            return "#ef5350"
        return "#9e9e9e"


@dataclass
class PlaceOrderRequest:
    symbol: str
    side: str
    order_type: str
    qty: str
    price: str | None = None
