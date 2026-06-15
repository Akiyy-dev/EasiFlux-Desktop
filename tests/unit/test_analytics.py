"""Unit tests for analytics service."""

from decimal import Decimal

from easiflux_desktop.models.trading import DesktopOrder, DesktopPosition, OrderStatus, PositionSide
from easiflux_desktop.services.analytics_service import AnalyticsService


def test_compute_stats():
    analytics = AnalyticsService()
    analytics.record_order(
        DesktopOrder(
            order_id="1",
            symbol="BTCUSDT",
            side="Buy",
            order_type="Limit",
            price=Decimal("50000"),
            qty=Decimal("0.01"),
            status=OrderStatus.FILLED,
        )
    )
    analytics.record_position(
        DesktopPosition(
            symbol="BTCUSDT",
            side=PositionSide.LONG,
            size=Decimal("0.01"),
            entry_price=Decimal("50000"),
            leverage=Decimal("10"),
            unrealised_pnl=Decimal("100"),
        )
    )
    stats = analytics.compute_stats()
    assert stats.total_orders == 1
    assert stats.filled_orders == 1
    assert stats.total_pnl == Decimal("100")
