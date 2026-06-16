"""Unit tests for multi-account manager behavior."""

from pathlib import Path

import pytest

from easiflux_desktop.core.errors import ValidationError
from easiflux_desktop.services.config_manager import ConfigManager
from easiflux_desktop.services.multi_account_manager import MultiAccountManager
from easiflux_desktop.storage.config_store import ConfigStore
from easiflux_desktop.storage.credential_store import CredentialStore


def _manager(tmp_path: Path) -> MultiAccountManager:
    config_manager = ConfigManager(ConfigStore(path=tmp_path / "config.toml"), CredentialStore())
    config_manager.load_config()
    return MultiAccountManager(config_manager)


@pytest.mark.asyncio
async def test_add_and_switch_account(tmp_path: Path):
    manager = _manager(tmp_path)

    assert manager.add_account("sub1") == "sub1"
    assert manager.active_account_id == "sub1"
    assert manager.list_accounts() == ["default", "sub1"]

    session = await manager.switch_account("default")

    assert session.account_id == "default"
    assert manager.active_account_id == "default"


@pytest.mark.asyncio
async def test_switch_unknown_account_rejected(tmp_path: Path):
    manager = _manager(tmp_path)

    with pytest.raises(ValidationError):
        await manager.switch_account("missing")
