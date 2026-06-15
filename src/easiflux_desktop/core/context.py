"""Application dependency injection container."""

from __future__ import annotations

from dataclasses import dataclass

from easiflux_desktop.adapters.rest_adapter import RestAdapter
from easiflux_desktop.adapters.sdk_client_factory import SdkClientFactory
from easiflux_desktop.adapters.ws_adapter import WsAdapter
from easiflux_desktop.core.command_bus import CommandBus
from easiflux_desktop.core.event_bus import EventBus
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


@dataclass
class AppContext:
    event_bus: EventBus
    command_bus: CommandBus
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

    @classmethod
    def create(cls) -> AppContext:
        event_bus = EventBus()
        command_bus = CommandBus(event_bus)

        config_store = ConfigStore()
        credential_store = CredentialStore()
        cache_store = CacheStore()

        config_manager = ConfigManager(config_store, credential_store)
        config_manager.load_config()

        sdk_factory = SdkClientFactory()
        rest_adapter = RestAdapter(sdk_factory)
        ws_adapter = WsAdapter(sdk_factory, event_bus)

        risk_manager = RiskManager()
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
        )
        ctx._wire_analytics(event_bus, analytics_service)
        return ctx

    @staticmethod
    def _wire_analytics(event_bus: EventBus, analytics: AnalyticsService) -> None:
        event_bus.subscribe("order.updated", analytics.record_order)
        event_bus.subscribe("order.created", analytics.record_order)
        event_bus.subscribe("position.updated", analytics.record_position)

    async def shutdown(self) -> None:
        await self.market_manager.stop_realtime()
        await self.connection_manager.disconnect()
        await self.multi_account_manager.disconnect_all()
