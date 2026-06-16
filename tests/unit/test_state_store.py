"""Unit tests for central state store reducers."""

from decimal import Decimal

from easiflux_desktop.core.event_bus import EventBus
from easiflux_desktop.core.state_store import StateStore
from easiflux_desktop.models.account import DesktopBalance
from easiflux_desktop.models.config import ConnectionStatus
from easiflux_desktop.models.market import DesktopTicker
from easiflux_desktop.models.trading import DesktopOrder, DesktopPosition, OrderStatus, PositionSide


def test_state_store_reduces_market_and_account_events(qapp):
    bus = EventBus()
    store = StateStore(bus, active_symbol="BTCUSDT", active_account_id="default")

    bus.publish(
        "ticker.updated",
        DesktopTicker(
            symbol="BTCUSDT",
            last_price=Decimal("50000"),
            bid_price=Decimal("49999"),
            ask_price=Decimal("50001"),
        ),
    )
    bus.publish("connection.status_changed", ConnectionStatus.CONNECTED)
    bus.publish("account.active_account_changed", "sub1")
    bus.publish(
        "balances.loaded",
        [DesktopBalance("USDT", Decimal("100"), Decimal("100"), Decimal("80"))],
    )
    qapp.processEvents()

    assert store.market.ticker("BTCUSDT").last_price == Decimal("50000")
    assert store.account.active_account_id == "sub1"
    assert store.account.connection_status == ConnectionStatus.CONNECTED
    assert store.account.total_equity == Decimal("100")


def test_state_store_reduces_position_and_order_events(qapp):
    bus = EventBus()
    store = StateStore(bus, active_symbol="BTCUSDT", active_account_id="default")

    position = DesktopPosition(
        symbol="BTCUSDT",
        side=PositionSide.LONG,
        size=Decimal("0.01"),
        entry_price=Decimal("50000"),
        leverage=Decimal("10"),
        unrealised_pnl=Decimal("12.5"),
    )
    order = DesktopOrder(
        order_id="1",
        symbol="BTCUSDT",
        side="Buy",
        order_type="Limit",
        price=Decimal("50000"),
        qty=Decimal("0.01"),
        status=OrderStatus.NEW,
    )

    bus.publish("position.updated", position)
    bus.publish("order.created", order)
    qapp.processEvents()

    assert store.positions.position_list() == [position]
    assert store.orders.open_orders() == [order]
