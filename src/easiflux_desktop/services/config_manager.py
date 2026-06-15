"""Configuration and credential management."""

from __future__ import annotations

from easiflux_desktop.models.config import ApiCredential, AppConfig
from easiflux_desktop.storage.config_store import ConfigStore
from easiflux_desktop.storage.credential_store import CredentialStore


class ConfigManager:
    def __init__(self, config_store: ConfigStore, credential_store: CredentialStore) -> None:
        self._config_store = config_store
        self._credential_store = credential_store
        self._config = AppConfig()

    @property
    def config(self) -> AppConfig:
        return self._config

    def load_config(self) -> AppConfig:
        self._config = self._config_store.load()
        return self._config

    def save_config(self, config: AppConfig | None = None) -> None:
        if config is not None:
            self._config = config
        self._config_store.save(self._config)

    def get_credentials(self, account_id: str | None = None) -> ApiCredential | None:
        account = account_id or self._config.active_account_id
        return self._credential_store.load(account)

    def set_credentials(self, account_id: str, credential: ApiCredential) -> None:
        self._credential_store.save(account_id, credential)
        if account_id not in self._config.accounts:
            self._config.accounts.append(account_id)
            self.save_config()

    def has_credentials(self, account_id: str | None = None) -> bool:
        account = account_id or self._config.active_account_id
        return self._credential_store.has_credentials(account)
