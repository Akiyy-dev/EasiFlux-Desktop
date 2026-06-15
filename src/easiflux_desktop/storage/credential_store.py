"""Secure API credential storage via system keyring."""

from __future__ import annotations

import json
import logging

import keyring
from keyring.errors import KeyringError

from easiflux_desktop.core.constants import DEFAULT_BASE_URL, KEYRING_SERVICE
from easiflux_desktop.core.errors import ConfigurationError
from easiflux_desktop.models.config import ApiCredential

logger = logging.getLogger(__name__)


class CredentialStore:
    def __init__(self, service: str = KEYRING_SERVICE) -> None:
        self._service = service

    def _username(self, account_id: str) -> str:
        return f"credentials:{account_id}"

    def save(self, account_id: str, credential: ApiCredential) -> None:
        payload = json.dumps(
            {
                "api_key": credential.api_key,
                "api_secret": credential.api_secret,
                "base_url": credential.base_url,
                "label": credential.label,
            }
        )
        try:
            keyring.set_password(self._service, self._username(account_id), payload)
        except KeyringError as exc:
            raise ConfigurationError("无法保存 API 凭证到系统密钥链", cause=exc) from exc

    def load(self, account_id: str) -> ApiCredential | None:
        try:
            raw = keyring.get_password(self._service, self._username(account_id))
        except KeyringError as exc:
            logger.warning("Keyring read failed: %s", exc)
            return None
        if not raw:
            return None
        data = json.loads(raw)
        return ApiCredential(
            api_key=data.get("api_key", ""),
            api_secret=data.get("api_secret", ""),
            base_url=data.get("base_url", DEFAULT_BASE_URL),
            label=data.get("label", account_id),
        )

    def delete(self, account_id: str) -> None:
        try:
            keyring.delete_password(self._service, self._username(account_id))
        except KeyringError:
            pass

    def has_credentials(self, account_id: str) -> bool:
        cred = self.load(account_id)
        return bool(cred and cred.api_key and cred.api_secret)
