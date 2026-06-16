"""Configuration and credential management."""

from __future__ import annotations

from easiflux_desktop.models.config import ApiCredential, AppConfig
from easiflux_desktop.services.risk_manager import RiskConfig
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

    def risk_config(self) -> RiskConfig:
        return RiskConfig(
            max_order_qty=self._config.risk_max_order_qty,
            max_price_deviation_pct=self._config.risk_max_price_deviation_pct,
            max_daily_orders=self._config.risk_max_daily_orders,
            enabled=self._config.risk_enabled,
        )

    def save_risk_config(self, risk_config: RiskConfig) -> None:
        self._config.risk_enabled = risk_config.enabled
        self._config.risk_max_order_qty = risk_config.max_order_qty
        self._config.risk_max_price_deviation_pct = risk_config.max_price_deviation_pct
        self._config.risk_max_daily_orders = risk_config.max_daily_orders
        self.save_config()
