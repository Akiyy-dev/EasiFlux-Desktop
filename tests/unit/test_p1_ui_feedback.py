"""Unit tests for P1 UI feedback behavior."""

from types import SimpleNamespace

import pytest

from easiflux_desktop.core.commands import RefreshMarketCommand, SetActiveSymbolCommand, SetKlineIntervalCommand
from easiflux_desktop.core.event_bus import EventBus
from easiflux_desktop.core.state_store import StateStore
from easiflux_desktop.models.account import DesktopBalance
from easiflux_desktop.models.market import DepthLevel, DesktopDepth, DesktopTicker
from easiflux_desktop.views.account_view import AccountView
from easiflux_desktop.views.market_view import MarketView
from easiflux_desktop.widgets.kline_chart import KlineChart
from easiflux_desktop.widgets.order_book import OrderBookWidget
from easiflux_desktop.widgets.order_panel import OrderPanel
from easiflux_desktop.widgets.order_table import OrderTable
from easiflux_desktop.widgets.ticker_bar import TickerBar


class FakeConfigManager:
    def __init__(self):
        self.config = SimpleNamespace(active_symbol="BTCUSDT", active_account_id="default", kline_interval="1")


class FakeCommandBus:
    def __init__(self, result=None):
        self.commands = []
        self.result = result or SimpleNamespace(success=True, data=[], error=None)

    async def execute(self, command):
        self.commands.append(command)
        return self.result

    def execute_background(self, command, on_complete=None):
        self.commands.append(command)
        if on_complete:
            on_complete(self.result)


def _ctx():
    event_bus = EventBus()
    config_manager = FakeConfigManager()
    return SimpleNamespace(
        event_bus=event_bus,
        command_bus=FakeCommandBus(),
        config_manager=config_manager,
        market_manager=SimpleNamespace(
            active_symbol=config_manager.config.active_symbol,
            watchlist_symbols=["BTCUSDT", "ETHUSDT"],
        ),
        state_store=StateStore(
            event_bus,
            active_symbol=config_manager.config.active_symbol,
            active_account_id=config_manager.config.active_account_id,
        ),
    )


def test_order_panel_cancelled_confirmation_does_not_dispatch(qapp):
    ctx = _ctx()
    panel = OrderPanel(ctx)
    panel._price.setText("50000")
    panel._confirm_order = lambda request: False

    panel._on_submit()
    qapp.processEvents()

    assert panel._status.text() == "已取消下单"
    assert ctx.command_bus.commands == []


def test_order_panel_limit_order_requires_price(qapp):
    ctx = _ctx()
    panel = OrderPanel(ctx)
    panel._confirm_order = lambda request: (_ for _ in ()).throw(AssertionError("confirmation should not open"))

    panel._on_submit()
    qapp.processEvents()

    assert panel._status.text() == "限价单必须填写价格"
    assert ctx.command_bus.commands == []


def test_order_table_busy_state_disables_refresh(qapp):
    table = OrderTable(_ctx())

    table._set_busy(True, "订单状态: 刷新中...")
    assert not table._refresh_btn.isEnabled()
    assert table._status.text() == "订单状态: 刷新中..."

    table._set_busy(False)
    assert table._refresh_btn.isEnabled()


def test_market_widgets_render_from_state_store(qapp):
    ctx = _ctx()
    ticker_bar = TickerBar(ctx)
    order_book = OrderBookWidget(ctx)

    ctx.event_bus.publish(
        "ticker.updated",
        DesktopTicker(symbol="BTCUSDT", last_price=100, bid_price=99, ask_price=101),
    )
    ctx.event_bus.publish(
        "depth.updated",
        DesktopDepth(
            symbol="BTCUSDT",
            bids=[DepthLevel(price=99, size=1)],
            asks=[DepthLevel(price=101, size=2)],
        ),
    )
    qapp.processEvents()

    assert ticker_bar._symbol.text() == "BTCUSDT"
    assert ticker_bar._last.text() == "最新: 100"
    assert order_book._table.item(0, 0).text() == "99"
    assert order_book._table.item(0, 2).text() == "101"


def test_kline_interval_change_dispatches_command(qapp):
    ctx = _ctx()
    chart = KlineChart(ctx)

    chart._on_interval_changed("15")

    assert isinstance(ctx.command_bus.commands[-1], SetKlineIntervalCommand)
    assert ctx.command_bus.commands[-1].interval == "15"


@pytest.mark.asyncio
async def test_market_view_switch_symbol_dispatches_command(qapp):
    ctx = _ctx()
    ctx.command_bus = FakeCommandBus(SimpleNamespace(success=True, data="ETHUSDT", error=None))
    view = MarketView(ctx)
    view._symbol_combo.setCurrentText("ETHUSDT")

    await view._switch_symbol()

    command = ctx.command_bus.commands[-1]
    assert isinstance(command, SetActiveSymbolCommand)
    assert command.symbol == "ETHUSDT"
    assert view._status.text() == "当前交易对: ETHUSDT"


@pytest.mark.asyncio
async def test_market_view_refresh_error_updates_status(qapp):
    ctx = _ctx()
    ctx.command_bus = FakeCommandBus(
        SimpleNamespace(success=False, data=None, error=SimpleNamespace(user_message="未连接"))
    )
    view = MarketView(ctx)

    await view._refresh_market()

    assert isinstance(ctx.command_bus.commands[-1], RefreshMarketCommand)
    assert view._status.text() == "行情刷新失败: 未连接"


def test_order_panel_symbol_tracks_active_market_state(qapp):
    ctx = _ctx()
    panel = OrderPanel(ctx)

    ctx.event_bus.publish("market.active_symbol_changed", "ETHUSDT")
    qapp.processEvents()

    assert panel._symbol.text() == "ETHUSDT"


@pytest.mark.asyncio
async def test_order_refresh_error_updates_status(qapp):
    ctx = _ctx()
    ctx.command_bus = FakeCommandBus(
        SimpleNamespace(success=False, data=None, error=SimpleNamespace(user_message="断开连接"))
    )
    table = OrderTable(ctx)

    await table._refresh()

    assert table._status.text() == "订单状态: 刷新失败 - 断开连接"


@pytest.mark.asyncio
async def test_account_refresh_error_updates_status(qapp):
    ctx = _ctx()
    ctx.command_bus = FakeCommandBus(
        SimpleNamespace(success=False, data=None, error=SimpleNamespace(user_message="未连接"))
    )
    ctx.state_store.account.balances["USDT"] = DesktopBalance(
        coin="USDT",
        equity=100,
        wallet_balance=100,
        available_balance=80,
    )
    view = AccountView(ctx)

    await view._refresh()

    assert view._status.text() == "账户状态: 刷新失败 - 未连接"
