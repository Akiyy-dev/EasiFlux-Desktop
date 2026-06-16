"""Integration-style tests for application command wiring."""

from types import SimpleNamespace

import pytest

from easiflux_desktop.core.command_bus import CommandBus
from easiflux_desktop.core.commands import (
    AddAccountCommand,
    CancelOrderCommand,
    ConnectCommand,
    ExportAnalyticsCommand,
    LoadKlinesCommand,
    PlaceOrderCommand,
    RefreshAccountCommand,
    RefreshMarketCommand,
    RefreshOrdersCommand,
    SaveConnectionSettingsCommand,
    SetActiveSymbolCommand,
    SetKlineIntervalCommand,
    SwitchAccountCommand,
    TestConnectionCommand,
    ToggleStrategyCommand,
    UpdateRiskConfigCommand,
)
from easiflux_desktop.core.context import AppContext
from easiflux_desktop.core.event_bus import EventBus
from easiflux_desktop.models.trading import PlaceOrderRequest
from easiflux_desktop.services.risk_manager import RiskConfig


class FakeConnectionManager:
    is_connected = True
    disconnected = 0

    async def connect(self, credential=None):
        self.is_connected = True
        return True

    async def disconnect(self):
        self.disconnected += 1
        self.is_connected = False

    async def test_connection(self, credential=None):
        return credential is not None


class FakeMarketManager:
    def __init__(self):
        self.active_symbol = "BTCUSDT"
        self.realtime_started = []
        self.realtime_stopped = 0
        self.snapshots = []

    async def start_realtime(self, symbol):
        self.realtime_started.append(symbol)

    async def stop_realtime(self):
        self.realtime_stopped += 1

    async def refresh_snapshot(self, symbol=None):
        snapshot = {"symbol": symbol or self.active_symbol}
        self.snapshots.append(snapshot)
        return snapshot

    async def get_klines(self, symbol=None, interval=None):
        return [symbol or self.active_symbol, interval or "1"]

    def set_active_symbol(self, symbol, *, persist=True):
        self.active_symbol = symbol
        return symbol


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


class FakeConfigManager:
    def __init__(self):
        self.config = SimpleNamespace(
            active_account_id="default",
            active_symbol="BTCUSDT",
            accounts=["default"],
            kline_interval="1",
            use_websocket=True,
            watchlist_symbols=["BTCUSDT", "ETHUSDT"],
        )
        self.saved_risk_config = None

    def add_account(self, account_id, *, make_active=True):
        if account_id not in self.config.accounts:
            self.config.accounts.append(account_id)
        if make_active:
            self.config.active_account_id = account_id
        return self.config

    def switch_account(self, account_id):
        self.config.active_account_id = account_id
        return self.config

    def save_connection_settings(self, *, active_symbol, use_websocket, credential=None, account_id=None):
        self.config.active_symbol = active_symbol
        self.config.use_websocket = use_websocket
        return self.config

    def set_kline_interval(self, interval):
        self.config.kline_interval = interval
        return self.config

    def save_risk_config(self, config):
        self.saved_risk_config = config


class FakeRiskManager:
    def __init__(self):
        self.config = None

    def update_config(self, config):
        self.config = config


class FakeStrategyManager:
    def __init__(self):
        self.enabled = False

    def enable(self, name):
        self.enabled = True

    def disable(self, name):
        self.enabled = False

    def list_strategies(self):
        return [SimpleNamespace(name="grid", enabled=self.enabled)]


class FakeMultiAccountManager:
    def __init__(self, config_manager):
        self.config_manager = config_manager

    def add_account(self, account_id, *, make_active=True):
        self.config_manager.add_account(account_id, make_active=make_active)
        return account_id

    async def switch_account(self, account_id):
        self.config_manager.switch_account(account_id)
        return SimpleNamespace(account_id=account_id)

    def list_accounts(self):
        return list(self.config_manager.config.accounts)


class FakeTradeLogStore:
    def export_text(self, filename, content):
        return f"/tmp/{filename}:{content}"


class FakeAnalyticsService:
    def export_orders_csv(self):
        return "order_id,symbol"


@pytest.mark.asyncio
async def test_app_context_registers_core_commands():
    event_bus = EventBus()
    command_bus = CommandBus(event_bus)
    market_manager = FakeMarketManager()
    config_manager = FakeConfigManager()
    risk_manager = FakeRiskManager()
    strategy_manager = FakeStrategyManager()
    ctx = SimpleNamespace(
        connection_manager=FakeConnectionManager(),
        config_manager=config_manager,
        market_manager=market_manager,
        account_manager=FakeAccountManager(),
        trading_manager=FakeTradingManager(),
        risk_manager=risk_manager,
        strategy_manager=strategy_manager,
        multi_account_manager=FakeMultiAccountManager(config_manager),
        trade_log_store=FakeTradeLogStore(),
        analytics_service=FakeAnalyticsService(),
        event_bus=event_bus,
    )
    AppContext._wire_commands(command_bus, ctx)

    assert (await command_bus.execute(TestConnectionCommand(object()))).success
    added = await command_bus.execute(AddAccountCommand("sub1"))
    assert added.data.active_account_id == "sub1"
    assert "sub1" in added.data.accounts
    switched = await command_bus.execute(SwitchAccountCommand("default"))
    assert switched.data == "default"
    assert config_manager.config.active_account_id == "default"
    assert (await command_bus.execute(ConnectCommand())).success
    assert market_manager.realtime_started[-1] == "BTCUSDT"
    assert market_manager.snapshots[-1] == {"symbol": "BTCUSDT"}
    assert (await command_bus.execute(LoadKlinesCommand(interval="5"))).data == ["BTCUSDT", "5"]
    assert (await command_bus.execute(RefreshMarketCommand("BTCUSDT"))).data == {"symbol": "BTCUSDT"}
    assert (await command_bus.execute(RefreshAccountCommand("ETHUSDT"))).data == {"symbol": "ETHUSDT"}
    assert (await command_bus.execute(RefreshOrdersCommand("ETHUSDT"))).data == ["ETHUSDT"]
    settings = await command_bus.execute(SaveConnectionSettingsCommand(active_symbol="SOLUSDT", use_websocket=False))
    assert settings.data.active_symbol == "SOLUSDT"
    assert not settings.data.use_websocket
    assert market_manager.active_symbol == "SOLUSDT"
    klines = await command_bus.execute(SetKlineIntervalCommand("15"))
    assert config_manager.config.kline_interval == "15"
    assert klines.data == ["SOLUSDT", "15"]

    request = PlaceOrderRequest(symbol="BTCUSDT", side="Buy", order_type="Market", qty="0.01")
    assert (await command_bus.execute(PlaceOrderCommand(request))).data == request
    assert (await command_bus.execute(CancelOrderCommand("BTCUSDT", "1"))).data == ("BTCUSDT", "1")
    assert (await command_bus.execute(SetActiveSymbolCommand("ETHUSDT"))).data == "ETHUSDT"
    assert market_manager.realtime_stopped == 2
    assert market_manager.realtime_started[-1] == "ETHUSDT"
    assert market_manager.snapshots[-1] == {"symbol": "ETHUSDT"}
    risk_config = RiskConfig(max_daily_orders=10)
    assert (await command_bus.execute(UpdateRiskConfigCommand(risk_config))).data == risk_config
    assert risk_manager.config == risk_config
    assert config_manager.saved_risk_config == risk_config
    assert (await command_bus.execute(ToggleStrategyCommand("grid", True))).data[0].enabled
    assert (await command_bus.execute(ExportAnalyticsCommand("orders.csv"))).data == "/tmp/orders.csv:order_id,symbol"
