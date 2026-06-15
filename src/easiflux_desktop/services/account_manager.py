"""Account balance and position management."""

from __future__ import annotations

import logging

from easiflux_desktop.adapters.rest_adapter import RestAdapter
from easiflux_desktop.adapters.ws_adapter import WsAdapter
from easiflux_desktop.core.event_bus import EventBus
from easiflux_desktop.models.account import DesktopAccount, DesktopBalance
from easiflux_desktop.models.trading import DesktopPosition
from easiflux_desktop.services.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class AccountManager:
    def __init__(
        self,
        rest: RestAdapter,
        ws: WsAdapter,
        config_manager: ConfigManager,
        event_bus: EventBus,
    ) -> None:
        self._rest = rest
        self._ws = ws
        self._config_manager = config_manager
        self._event_bus = event_bus
        self._balances: list[DesktopBalance] = []
        self._positions: list[DesktopPosition] = []

    @property
    def balances(self) -> list[DesktopBalance]:
        return list(self._balances)

    @property
    def positions(self) -> list[DesktopPosition]:
        return list(self._positions)

    async def get_balances(self) -> list[DesktopBalance]:
        self._balances = await self._rest.get_balances()
        for balance in self._balances:
            self._event_bus.publish("balance.updated", balance)
        return self._balances

    async def get_positions(self, symbol: str | None = None) -> list[DesktopPosition]:
        self._positions = await self._rest.get_positions(symbol)
        for position in self._positions:
            self._event_bus.publish("position.updated", position)
        return self._positions

    async def refresh_account(self, symbol: str | None = None) -> DesktopAccount:
        balances = await self.get_balances()
        await self.get_positions(symbol)
        account_id = self._config_manager.config.active_account_id
        cred = self._config_manager.get_credentials(account_id)
        label = cred.label if cred else account_id
        return DesktopAccount(account_id=account_id, label=label, balances=balances)

    async def subscribe_updates(self) -> None:
        await self._ws.subscribe_positions()
        await self._ws.subscribe_balances()
