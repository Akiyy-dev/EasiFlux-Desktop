"""SDK connection lifecycle management."""

from __future__ import annotations

import logging

from easiflux_desktop.adapters.sdk_client_factory import SdkClientFactory
from easiflux_desktop.core.errors import AuthenticationError, ConfigurationError
from easiflux_desktop.core.event_bus import EventBus
from easiflux_desktop.models.config import ApiCredential, ConnectionStatus
from easiflux_desktop.services.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(
        self,
        factory: SdkClientFactory,
        config_manager: ConfigManager,
        event_bus: EventBus,
    ) -> None:
        self._factory = factory
        self._config_manager = config_manager
        self._event_bus = event_bus
        self._status = ConnectionStatus.DISCONNECTED

    @property
    def status(self) -> ConnectionStatus:
        return self._status

    @property
    def is_connected(self) -> bool:
        return self._status == ConnectionStatus.CONNECTED

    def _set_status(self, status: ConnectionStatus) -> None:
        self._status = status
        self._event_bus.publish("connection.status_changed", status, sticky=True)

    async def connect(self, credential: ApiCredential | None = None) -> bool:
        self._set_status(ConnectionStatus.CONNECTING)
        cred = credential or self._config_manager.get_credentials()
        if cred is None:
            self._set_status(ConnectionStatus.ERROR)
            raise ConfigurationError("未找到 API 凭证，请先在设置中配置")

        try:
            await self._factory.create(cred)
            ok = await self._factory.health_check()
            if not ok:
                raise AuthenticationError("连接测试失败")
            self._set_status(ConnectionStatus.CONNECTED)
            return True
        except Exception:
            self._set_status(ConnectionStatus.ERROR)
            await self._factory.destroy()
            raise

    async def disconnect(self) -> None:
        await self._factory.destroy()
        self._set_status(ConnectionStatus.DISCONNECTED)

    async def test_connection(self, credential: ApiCredential | None = None) -> bool:
        cred = credential or self._config_manager.get_credentials()
        if cred is None:
            raise ConfigurationError("未找到 API 凭证")

        temp_factory = SdkClientFactory()
        try:
            await temp_factory.create(cred)
            return await temp_factory.health_check()
        finally:
            await temp_factory.destroy()
