"""Multi-account session management."""

from __future__ import annotations

import logging

from easiflux_desktop.adapters.sdk_client_factory import SdkClientFactory
from easiflux_desktop.core.errors import ValidationError
from easiflux_desktop.models.config import ConnectionStatus
from easiflux_desktop.services.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class AccountSession:
    def __init__(self, account_id: str, factory: SdkClientFactory) -> None:
        self.account_id = account_id
        self.factory = factory
        self.status = ConnectionStatus.DISCONNECTED


class MultiAccountManager:
    def __init__(self, config_manager: ConfigManager) -> None:
        self._config_manager = config_manager
        self._sessions: dict[str, AccountSession] = {}
        self._active_id: str = config_manager.config.active_account_id

    @property
    def active_account_id(self) -> str:
        return self._active_id

    def list_accounts(self) -> list[str]:
        return list(self._config_manager.config.accounts)

    def add_account(self, account_id: str, *, make_active: bool = True) -> str:
        config = self._config_manager.add_account(account_id, make_active=make_active)
        if make_active:
            self._active_id = config.active_account_id
        return self._config_manager.normalize_account_id(account_id)

    async def switch_account(self, account_id: str) -> AccountSession:
        try:
            config = self._config_manager.switch_account(account_id)
        except ValidationError:
            raise
        except Exception as exc:
            raise ValidationError(str(exc)) from exc

        self._active_id = config.active_account_id
        if self._active_id not in self._sessions:
            self._sessions[self._active_id] = AccountSession(self._active_id, SdkClientFactory())

        return self._sessions[self._active_id]

    async def connect_account(self, account_id: str) -> bool:
        session = await self.switch_account(account_id)
        cred = self._config_manager.get_credentials(account_id)
        if cred is None:
            return False
        await session.factory.create(cred)
        session.status = ConnectionStatus.CONNECTED
        return True

    def get_session(self, account_id: str | None = None) -> AccountSession | None:
        aid = account_id or self._active_id
        return self._sessions.get(aid)

    async def disconnect_all(self) -> None:
        for session in self._sessions.values():
            await session.factory.destroy()
            session.status = ConnectionStatus.DISCONNECTED
