"""Trading statistics and PnL analytics."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal

from easiflux_desktop.models.trading import DesktopOrder, DesktopPosition


@dataclass
class TradeStats:
    total_orders: int = 0
    filled_orders: int = 0
    cancelled_orders: int = 0
    total_pnl: Decimal = Decimal("0")
    win_count: int = 0
    loss_count: int = 0
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class AnalyticsService:
    def __init__(self) -> None:
        self._orders: list[DesktopOrder] = []
        self._positions: list[DesktopPosition] = []

    def record_order(self, order: DesktopOrder) -> None:
        existing = next((o for o in self._orders if o.order_id == order.order_id), None)
        if existing:
            self._orders.remove(existing)
        self._orders.append(order)

    def record_position(self, position: DesktopPosition) -> None:
        existing = next((p for p in self._positions if p.symbol == position.symbol), None)
        if existing:
            self._positions.remove(existing)
        self._positions.append(position)

    def compute_stats(self) -> TradeStats:
        stats = TradeStats()
        stats.total_orders = len(self._orders)
        for order in self._orders:
            if order.status.value == "Filled":
                stats.filled_orders += 1
            elif order.status.value == "Cancelled":
                stats.cancelled_orders += 1

        for pos in self._positions:
            stats.total_pnl += pos.unrealised_pnl
            if pos.unrealised_pnl > 0:
                stats.win_count += 1
            elif pos.unrealised_pnl < 0:
                stats.loss_count += 1

        return stats

    def export_orders_csv(self) -> str:
        lines = ["order_id,symbol,side,type,price,qty,status"]
        for o in self._orders:
            lines.append(f"{o.order_id},{o.symbol},{o.side},{o.order_type},{o.price},{o.qty},{o.status.value}")
        return "\n".join(lines)
