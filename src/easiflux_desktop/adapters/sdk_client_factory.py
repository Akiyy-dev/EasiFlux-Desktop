"""Factory for AsyncEasiFluxSDK client lifecycle."""

from __future__ import annotations

import logging

from easiflux_sdk import AsyncEasiFluxSDK, AuthConfig, ResponseConfig

from easiflux_desktop.core.errors import ConfigurationError
from easiflux_desktop.models.config import ApiCredential

logger = logging.getLogger(__name__)


class SdkClientFactory:
    def __init__(self) -> None:
        self._client: AsyncEasiFluxSDK | None = None
        self._credential: ApiCredential | None = None

    @property
    def client(self) -> AsyncEasiFluxSDK | None:
        return self._client

    @property
    def is_initialized(self) -> bool:
        return self._client is not None

    async def create(self, credential: ApiCredential) -> AsyncEasiFluxSDK:
        if self._client is not None:
            await self.destroy()

        if not credential.api_key or not credential.api_secret:
            raise ConfigurationError("API Key 和 Secret 不能为空")

        self._client = AsyncEasiFluxSDK(
            api_key=credential.api_key,
            api_secret=credential.api_secret,
            base_url=credential.base_url,
            auth_config=AuthConfig(signature_encoding="hex"),
            response_config=ResponseConfig(
                code_fields=("code",),
                success_codes=(0, "0"),
                message_fields=("msg", "message"),
            ),
            sync_on_init=True,
            auto_sync_time=True,
        )
        self._credential = credential
        logger.info("SDK client created for %s", credential.base_url)
        return self._client

    async def destroy(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None
            self._credential = None
            logger.info("SDK client destroyed")

    async def health_check(self) -> bool:
        if self._client is None:
            return False
        try:
            await self._client.get_server_time()
            return True
        except Exception as exc:
            logger.warning("Health check failed: %s", exc)
            return False

    def require_client(self) -> AsyncEasiFluxSDK:
        if self._client is None:
            raise ConfigurationError("SDK 未连接，请先在设置中配置并连接 API")
        return self._client
