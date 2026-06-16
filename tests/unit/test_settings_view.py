"""Unit tests for settings view save behavior."""

from types import SimpleNamespace

import pytest

from easiflux_desktop.core.commands import AddAccountCommand, SaveConnectionSettingsCommand, SwitchAccountCommand
from easiflux_desktop.core.event_bus import EventBus
from easiflux_desktop.core.state_store import StateStore
from easiflux_desktop.views.settings_view import SettingsView


class FakeConfigManager:
    def __init__(self):
        self.config = SimpleNamespace(
            active_account_id="default",
            active_symbol="BTCUSDT",
            accounts=["default"],
            kline_interval="1",
            use_websocket=True,
        )
        self.credentials = {}

    def get_credentials(self):
        return self.credentials.get(self.config.active_account_id)


class FakeCommandBus:
    def __init__(self):
        self.commands = []

    def execute_background(self, command, on_complete=None):
        self.commands.append(command)
        if on_complete:
            on_complete(SimpleNamespace(success=True, data=SimpleNamespace(), error=None))

    async def execute(self, command):
        self.commands.append(command)
        if isinstance(command, AddAccountCommand):
            if command.account_id not in self.config_manager.config.accounts:
                self.config_manager.config.accounts.append(command.account_id)
            if command.switch:
                self.config_manager.config.active_account_id = command.account_id
            return SimpleNamespace(success=True, data=self.config_manager.config, error=None)
        if isinstance(command, SwitchAccountCommand):
            self.config_manager.config.active_account_id = command.account_id
            return SimpleNamespace(success=True, data=command.account_id, error=None)
        return SimpleNamespace(success=True, data=SimpleNamespace(), error=None)


def _ctx():
    event_bus = EventBus()
    config_manager = FakeConfigManager()
    command_bus = FakeCommandBus()
    command_bus.config_manager = config_manager
    return SimpleNamespace(
        config_manager=config_manager,
        command_bus=command_bus,
        event_bus=event_bus,
        state_store=StateStore(
            event_bus,
            active_symbol=config_manager.config.active_symbol,
            active_account_id=config_manager.config.active_account_id,
        ),
    )


def test_settings_save_without_credentials_only_saves_config(qapp):
    ctx = _ctx()
    view = SettingsView(ctx)

    view._symbol.setText("ETHUSDT")

    assert view._on_save()
    assert ctx.command_bus.commands
    command = ctx.command_bus.commands[-1]
    assert isinstance(command, SaveConnectionSettingsCommand)
    assert command.active_symbol == "ETHUSDT"
    assert command.credential is None
    assert view._status.text() == "配置已保存"


def test_settings_busy_state_disables_actions(qapp):
    ctx = _ctx()
    view = SettingsView(ctx)

    view._set_busy(True, "连接中...")
    assert not view._save_btn.isEnabled()
    assert not view._test_btn.isEnabled()
    assert not view._connect_btn.isEnabled()
    assert view._status.text() == "连接中..."

    view._set_busy(False)
    assert view._save_btn.isEnabled()
    assert view._test_btn.isEnabled()
    assert view._connect_btn.isEnabled()
    assert view._switch_account_btn.isEnabled()
    assert view._add_account_btn.isEnabled()


@pytest.mark.asyncio
async def test_settings_add_account_switches_active_account(qapp):
    ctx = _ctx()
    view = SettingsView(ctx)

    view._new_account.setText("sub1")
    await view._on_add_account()

    assert isinstance(ctx.command_bus.commands[-1], AddAccountCommand)
    assert ctx.config_manager.config.active_account_id == "sub1"
    assert view._account_combo.currentText() == "sub1"
    assert view._status.text() == "已添加账户: sub1"


@pytest.mark.asyncio
async def test_settings_switch_account_clears_missing_credentials(qapp):
    ctx = _ctx()
    ctx.config_manager.config.accounts.append("sub1")
    ctx.config_manager.credentials["default"] = SimpleNamespace(
        api_key="key",
        api_secret="secret",
        base_url="https://example.test",
    )
    view = SettingsView(ctx)
    assert view._api_key.text() == "key"

    view._account_combo.setCurrentText("sub1")
    await view._on_switch_account()

    assert isinstance(ctx.command_bus.commands[-1], SwitchAccountCommand)
    assert ctx.config_manager.config.active_account_id == "sub1"
    assert view._api_key.text() == ""
    assert view._api_secret.text() == ""
    assert view._status.text() == "已切换账户: sub1"
