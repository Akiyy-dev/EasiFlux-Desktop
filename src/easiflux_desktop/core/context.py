"""Application dependency injection container."""

from __future__ import annotations

from dataclasses import dataclass

from easiflux_desktop.adapters.rest_adapter import RestAdapter
from easiflux_desktop.adapters.sdk_client_factory import SdkClientFactory
from easiflux_desktop.adapters.ws_adapter import WsAdapter
from easiflux_desktop.core.command_bus import CommandBus
from easiflux_desktop.core.commands import (
    CancelOrderCommand,
    ConnectCommand,
    ExportAnalyticsCommand,
    LoadKlinesCommand,
    PlaceOrderCommand,
    RefreshAccountCommand,
    RefreshOrdersCommand,
    SetActiveSymbolCommand,
    TestConnectionCommand,
    ToggleStrategyCommand,
    UpdateRiskConfigCommand,
)
from easiflux_desktop.core.event_bus import EventBus
from easiflux_desktop.core.state_store import StateStore
from easiflux_desktop.services.account_manager import AccountManager
from easiflux_desktop.services.analytics_service import AnalyticsService
from easiflux_desktop.services.config_manager import ConfigManager
from easiflux_desktop.services.connection_manager import ConnectionManager
from easiflux_desktop.services.market_manager import MarketManager
from easiflux_desktop.services.multi_account_manager import MultiAccountManager
from easiflux_desktop.services.risk_manager import RiskManager
from easiflux_desktop.services.strategy_manager import GridStrategy, StrategyManager
from easiflux_desktop.services.trading_manager import TradingManager
from easiflux_desktop.storage.cache_store import CacheStore
from easiflux_desktop.storage.config_store import ConfigStore
from easiflux_desktop.storage.credential_store import CredentialStore
from easiflux_desktop.storage.trade_log_store import TradeLogStore


@dataclass
class AppContext:
    event_bus: EventBus
    command_bus: CommandBus
    state_store: StateStore
    config_manager: ConfigManager
    connection_manager: ConnectionManager
    market_manager: MarketManager
    trading_manager: TradingManager
    account_manager: AccountManager
    risk_manager: RiskManager
    strategy_manager: StrategyManager
    multi_account_manager: MultiAccountManager
    analytics_service: AnalyticsService
    sdk_factory: SdkClientFactory
    rest_adapter: RestAdapter
    ws_adapter: WsAdapter
    cache_store: CacheStore
    trade_log_store: TradeLogStore

    @classmethod
    def create(cls) -> AppContext:
        event_bus = EventBus()
        command_bus = CommandBus(event_bus)

        config_store = ConfigStore()
        credential_store = CredentialStore()
        cache_store = CacheStore()
        trade_log_store = TradeLogStore()

        config_manager = ConfigManager(config_store, credential_store)
        config_manager.load_config()
        state_store = StateStore(
            event_bus,
            active_symbol=config_manager.config.active_symbol,
            active_account_id=config_manager.config.active_account_id,
        )

        sdk_factory = SdkClientFactory()
        rest_adapter = RestAdapter(sdk_factory)
        ws_adapter = WsAdapter(sdk_factory, event_bus)

        risk_manager = RiskManager(config_manager.risk_config())
        connection_manager = ConnectionManager(sdk_factory, config_manager, event_bus)
        market_manager = MarketManager(rest_adapter, ws_adapter, cache_store, config_manager, event_bus)
        trading_manager = TradingManager(rest_adapter, ws_adapter, risk_manager, event_bus)
        account_manager = AccountManager(rest_adapter, ws_adapter, config_manager, event_bus)
        strategy_manager = StrategyManager(event_bus)
        multi_account_manager = MultiAccountManager(config_manager)
        analytics_service = AnalyticsService()

        strategy_manager.register(GridStrategy(
            symbol=config_manager.config.active_symbol,
            grid_price="0",
            qty="0.001",
        ))

        ctx = cls(
            event_bus=event_bus,
            command_bus=command_bus,
            state_store=state_store,
            config_manager=config_manager,
            connection_manager=connection_manager,
            market_manager=market_manager,
            trading_manager=trading_manager,
            account_manager=account_manager,
            risk_manager=risk_manager,
            strategy_manager=strategy_manager,
            multi_account_manager=multi_account_manager,
            analytics_service=analytics_service,
            sdk_factory=sdk_factory,
            rest_adapter=rest_adapter,
            ws_adapter=ws_adapter,
            cache_store=cache_store,
            trade_log_store=trade_log_store,
        )
        ctx._wire_order_sinks(event_bus, analytics_service, trade_log_store)
        ctx._wire_commands(command_bus, ctx)
        return ctx

    @staticmethod
    def _wire_order_sinks(event_bus: EventBus, analytics: AnalyticsService, trade_log_store: TradeLogStore) -> None:
        event_bus.subscribe("order.updated", analytics.record_order)
        event_bus.subscribe("order.created", analytics.record_order)
        event_bus.subscribe("position.updated", analytics.record_position)
        event_bus.subscribe("order.updated", trade_log_store.record_order)
        event_bus.subscribe("order.created", trade_log_store.record_order)

    @staticmethod
    def _wire_commands(command_bus: CommandBus, ctx: AppContext) -> None:
        async def _connect(command: ConnectCommand) -> bool:
            ok = await ctx.connection_manager.connect(command.credential)
            if command.start_realtime:
                symbol = ctx.config_manager.config.active_symbol
                await ctx.market_manager.start_realtime(symbol)
                await ctx.market_manager.get_klines(symbol)
                await ctx.account_manager.refresh_account(symbol)
                await ctx.trading_manager.refresh_orders(symbol)
            return ok

        async def _test_connection(command: TestConnectionCommand) -> bool:
            return await ctx.connection_manager.test_connection(command.credential)

        async def _place_order(command: PlaceOrderCommand):
            return await ctx.trading_manager.place_order(command.request)

        async def _cancel_order(command: CancelOrderCommand):
            return await ctx.trading_manager.cancel_order(command.symbol, command.order_id)

        async def _refresh_orders(command: RefreshOrdersCommand):
            return await ctx.trading_manager.refresh_orders(command.symbol)

        async def _refresh_account(command: RefreshAccountCommand):
            symbol = command.symbol or ctx.market_manager.active_symbol
            return await ctx.account_manager.refresh_account(symbol)

        async def _load_klines(command: LoadKlinesCommand):
            return await ctx.market_manager.get_klines(command.symbol, command.interval)

        async def _set_active_symbol(command: SetActiveSymbolCommand) -> str:
            ctx.market_manager.set_active_symbol(command.symbol)
            return command.symbol

        async def _update_risk_config(command: UpdateRiskConfigCommand):
            ctx.risk_manager.update_config(command.config)
            ctx.config_manager.save_risk_config(command.config)
            ctx.event_bus.publish("risk.config_updated", command.config, sticky=True)
            return command.config

        async def _toggle_strategy(command: ToggleStrategyCommand):
            if command.enabled:
                ctx.strategy_manager.enable(command.name)
            else:
                ctx.strategy_manager.disable(command.name)
            states = ctx.strategy_manager.list_strategies()
            ctx.event_bus.publish("strategy.states_updated", states, sticky=True)
            return states

        async def _export_analytics(command: ExportAnalyticsCommand):
            return ctx.trade_log_store.export_text(
                command.filename,
                ctx.analytics_service.export_orders_csv(),
            )

        command_bus.register(ConnectCommand, _connect)
        command_bus.register(TestConnectionCommand, _test_connection)
        command_bus.register(PlaceOrderCommand, _place_order)
        command_bus.register(CancelOrderCommand, _cancel_order)
        command_bus.register(RefreshOrdersCommand, _refresh_orders)
        command_bus.register(RefreshAccountCommand, _refresh_account)
        command_bus.register(LoadKlinesCommand, _load_klines)
        command_bus.register(SetActiveSymbolCommand, _set_active_symbol)
        command_bus.register(UpdateRiskConfigCommand, _update_risk_config)
        command_bus.register(ToggleStrategyCommand, _toggle_strategy)
        command_bus.register(ExportAnalyticsCommand, _export_analytics)

    async def shutdown(self) -> None:
        await self.market_manager.stop_realtime()
        await self.connection_manager.disconnect()
        await self.multi_account_manager.disconnect_all()
