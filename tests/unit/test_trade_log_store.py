"""Unit tests for persistent trade log storage."""

from decimal import Decimal

from easiflux_desktop.models.trading import DesktopOrder, OrderStatus
from easiflux_desktop.storage.trade_log_store import TradeLogStore


def test_trade_log_store_records_order_and_exports_text(tmp_path):
    store = TradeLogStore(directory=tmp_path)
    order = DesktopOrder(
        order_id="1",
        symbol="BTCUSDT",
        side="Buy",
        order_type="Limit",
        price=Decimal("50000"),
        qty=Decimal("0.01"),
        status=OrderStatus.NEW,
    )

    store.record_order(order)
    exported = store.export_text("orders.csv", "order_id,symbol\n1,BTCUSDT")

    content = store.orders_path.read_text(encoding="utf-8")
    assert "order_id" in content
    assert "BTCUSDT" in content
    assert exported.read_text(encoding="utf-8") == "order_id,symbol\n1,BTCUSDT"
