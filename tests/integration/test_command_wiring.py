"""Integration-style tests for application command wiring."""

from types import SimpleNamespace

import pytest

from easiflux_desktop.core.command_bus import CommandBus
from easiflux_desktop.core.commands import (
    CancelOrderCommand,
    ConnectCommand,
    LoadKlinesCommand,
    PlaceOrderCommand,
    RefreshAccountCommand,
    RefreshOrdersCommand,
    SetActiveSymbolCommand,
    TestConnectionCommand,
)
from easiflux_desktop.core.context import AppContext
from easiflux_desktop.core.event_bus import EventBus
from easiflux_desktop.models.trading import PlaceOrderRequest


class FakeConnectionManager:
    async def connect(self, credential=None):
        return True

    async def test_connection(self, credential=None):
        return credential is not None


class FakeMarketManager:
    def __init__(self):
        self.active_symbol = "BTCUSDT"
        self.realtime_started = False

    async def start_realtime(self, symbol):
        self.realtime_started = symbol == "BTCUSDT"

    async def get_klines(self, symbol=None, interval=None):
        return [symbol or self.active_symbol, interval or "1"]

    def set_active_symbol(self, symbol):
        self.active_symbol = symbol


class FakeAccountManager:
    async def refresh_account(self, symbol=None):
        return {"symbol": symbol}


class FakeTradingManager:
    async def refresh_orders(self, symbol=None):
        return [symbol]

    async def place_order(self, request):
        return request

    async def cancel_order(self, symbol, order_id):
        return symbol, order_id


@pytest.mark.asyncio
async def test_app_context_registers_core_commands():
    command_bus = CommandBus(EventBus())
    market_manager = FakeMarketManager()
    ctx = SimpleNamespace(
        connection_manager=FakeConnectionManager(),
        config_manager=SimpleNamespace(config=SimpleNamespace(active_symbol="BTCUSDT")),
        market_manager=market_manager,
        account_manager=FakeAccountManager(),
        trading_manager=FakeTradingManager(),
    )
    AppContext._wire_commands(command_bus, ctx)

    assert (await command_bus.execute(TestConnectionCommand(object()))).success
    assert (await command_bus.execute(ConnectCommand())).success
    assert market_manager.realtime_started
    assert (await command_bus.execute(LoadKlinesCommand(interval="5"))).data == ["BTCUSDT", "5"]
    assert (await command_bus.execute(RefreshAccountCommand("ETHUSDT"))).data == {"symbol": "ETHUSDT"}
    assert (await command_bus.execute(RefreshOrdersCommand("ETHUSDT"))).data == ["ETHUSDT"]

    request = PlaceOrderRequest(symbol="BTCUSDT", side="Buy", order_type="Market", qty="0.01")
    assert (await command_bus.execute(PlaceOrderCommand(request))).data == request
    assert (await command_bus.execute(CancelOrderCommand("BTCUSDT", "1"))).data == ("BTCUSDT", "1")
    assert (await command_bus.execute(SetActiveSymbolCommand("ETHUSDT"))).data == "ETHUSDT"
