"""API settings and connection configuration view."""

from __future__ import annotations

import asyncio

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from easiflux_desktop.core.commands import (
    AddAccountCommand,
    ConnectCommand,
    SaveConnectionSettingsCommand,
    SwitchAccountCommand,
    TestConnectionCommand,
)
from easiflux_desktop.core.constants import DEFAULT_BASE_URL
from easiflux_desktop.core.context import AppContext
from easiflux_desktop.core.state_store import MarketState
from easiflux_desktop.models.config import ApiCredential


class SettingsView(QGroupBox):
    def __init__(self, ctx: AppContext, parent=None) -> None:
        super().__init__("设置", parent)
        self._ctx = ctx
        layout = QVBoxLayout(self)
        account_group = QGroupBox("账户")
        account_layout = QFormLayout(account_group)
        self._account_combo = QComboBox()
        self._sync_accounts()
        self._switch_account_btn = QPushButton("切换账户")
        self._switch_account_btn.clicked.connect(lambda: asyncio.create_task(self._on_switch_account()))
        switch_row = QHBoxLayout()
        switch_row.addWidget(self._account_combo)
        switch_row.addWidget(self._switch_account_btn)
        account_layout.addRow("当前账户", switch_row)

        self._new_account = QLineEdit()
        self._new_account.setPlaceholderText("例如: sub-account-1")
        self._add_account_btn = QPushButton("添加账户")
        self._add_account_btn.clicked.connect(lambda: asyncio.create_task(self._on_add_account()))
        add_row = QHBoxLayout()
        add_row.addWidget(self._new_account)
        add_row.addWidget(self._add_account_btn)
        account_layout.addRow("新增账户", add_row)
        layout.addWidget(account_group)

        form = QFormLayout()

        self._api_key = QLineEdit()
        self._api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self._api_secret = QLineEdit()
        self._api_secret.setEchoMode(QLineEdit.EchoMode.Password)
        self._base_url = QLineEdit(DEFAULT_BASE_URL)
        self._symbol = QLineEdit(ctx.config_manager.config.active_symbol)
        self._use_ws = QCheckBox("使用 WebSocket 实时推送")
        self._use_ws.setChecked(ctx.config_manager.config.use_websocket)

        form.addRow("API Key", self._api_key)
        form.addRow("API Secret", self._api_secret)
        form.addRow("Base URL", self._base_url)
        form.addRow("默认交易对", self._symbol)
        form.addRow("", self._use_ws)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        self._save_btn = QPushButton("保存")
        self._save_btn.clicked.connect(self._on_save)
        self._test_btn = QPushButton("测试连接")
        self._test_btn.clicked.connect(lambda: asyncio.create_task(self._on_test()))
        self._connect_btn = QPushButton("连接")
        self._connect_btn.clicked.connect(lambda: asyncio.create_task(self._on_connect()))
        btn_row.addWidget(self._save_btn)
        btn_row.addWidget(self._test_btn)
        btn_row.addWidget(self._connect_btn)
        layout.addLayout(btn_row)

        self._status = QLabel("")
        layout.addWidget(self._status)

        self._load_existing()
        ctx.event_bus.subscribe("state.market.updated", self._on_market_state)
        ctx.event_bus.subscribe("accounts.updated", lambda _: self._sync_accounts())
        ctx.event_bus.subscribe("state.account.updated", lambda _: self._sync_accounts())

    def _sync_accounts(self) -> None:
        config = self._ctx.config_manager.config
        self._account_combo.clear()
        self._account_combo.addItems(config.accounts)
        self._account_combo.setCurrentText(config.active_account_id)

    def _current_account_id(self) -> str:
        return self._account_combo.currentText().strip()

    def _load_existing(self) -> None:
        self._api_key.clear()
        self._api_secret.clear()
        self._base_url.setText(DEFAULT_BASE_URL)
        cred = self._ctx.config_manager.get_credentials()
        if cred:
            self._api_key.setText(cred.api_key)
            self._api_secret.setText(cred.api_secret)
            self._base_url.setText(cred.base_url)

    def _build_credential(self) -> ApiCredential:
        return ApiCredential(
            api_key=self._api_key.text().strip(),
            api_secret=self._api_secret.text().strip(),
            base_url=self._base_url.text().strip() or DEFAULT_BASE_URL,
        )

    def _build_save_command(self) -> SaveConnectionSettingsCommand:
        cred = self._build_credential()
        credential = cred if cred.api_key or cred.api_secret else None
        return SaveConnectionSettingsCommand(
            active_symbol=self._symbol.text().strip(),
            use_websocket=self._use_ws.isChecked(),
            credential=credential,
            account_id=self._current_account_id(),
        )

    def _on_save(self) -> bool:
        try:
            command = self._build_save_command()
            self._set_busy(True, "保存中...")
            self._ctx.command_bus.execute_background(command, self._on_save_complete)
            return True
        except Exception as exc:
            self._status.setText(f"保存失败: {exc}")
            QMessageBox.warning(self, "保存失败", str(exc))
            return False

    def _on_save_complete(self, result) -> None:
        self._set_busy(False)
        if result.success:
            self._status.setText("配置已保存")
        elif result.error:
            self._status.setText(f"保存失败: {result.error.user_message}")
            QMessageBox.warning(self, "保存失败", result.error.user_message)

    async def _save_settings(self) -> bool:
        result = await self._ctx.command_bus.execute(self._build_save_command())
        if result.success:
            self._status.setText("配置已保存")
            return True
        if result.error:
            self._status.setText(f"保存失败: {result.error.user_message}")
            QMessageBox.warning(self, "保存失败", result.error.user_message)
        return False

    async def _on_test(self) -> None:
        cred = self._build_credential()
        self._set_busy(True, "测试中...")
        self._status.setText("测试中...")
        try:
            result = await self._ctx.command_bus.execute(TestConnectionCommand(cred))
            ok = bool(result.success and result.data)
            self._status.setText("连接测试成功" if ok else "连接测试失败")
        except Exception as exc:
            self._status.setText(f"测试失败: {exc}")
        finally:
            self._set_busy(False)

    async def _on_connect(self) -> None:
        if not await self._save_settings():
            return
        cred = self._build_credential()
        self._set_busy(True, "连接中...")
        self._status.setText("连接中...")
        try:
            result = await self._ctx.command_bus.execute(ConnectCommand(cred))
            if result.success:
                self._status.setText("已连接")
            elif result.error:
                self._status.setText(f"连接失败: {result.error.user_message}")
                QMessageBox.warning(self, "连接失败", result.error.user_message)
        except Exception as exc:
            self._status.setText(f"连接失败: {exc}")
            QMessageBox.warning(self, "连接失败", str(exc))
        finally:
            self._set_busy(False)

    async def _on_add_account(self) -> None:
        account_id = self._new_account.text().strip()
        self._set_busy(True, "正在添加账户...")
        try:
            result = await self._ctx.command_bus.execute(AddAccountCommand(account_id))
            if result.success:
                self._new_account.clear()
                self._sync_accounts()
                self._load_existing()
                self._status.setText(f"已添加账户: {result.data.active_account_id}")
            elif result.error:
                self._status.setText(f"添加账户失败: {result.error.user_message}")
        finally:
            self._set_busy(False)

    async def _on_switch_account(self) -> None:
        account_id = self._current_account_id()
        self._set_busy(True, "正在切换账户...")
        try:
            result = await self._ctx.command_bus.execute(SwitchAccountCommand(account_id))
            if result.success:
                self._sync_accounts()
                self._load_existing()
                self._status.setText(f"已切换账户: {result.data}")
            elif result.error:
                self._status.setText(f"切换账户失败: {result.error.user_message}")
        finally:
            self._set_busy(False)

    def _set_busy(self, busy: bool, label: str | None = None) -> None:
        self._save_btn.setEnabled(not busy)
        self._test_btn.setEnabled(not busy)
        self._connect_btn.setEnabled(not busy)
        self._switch_account_btn.setEnabled(not busy)
        self._add_account_btn.setEnabled(not busy)
        if label:
            self._status.setText(label)

    def _on_market_state(self, state: MarketState) -> None:
        if not self._symbol.hasFocus() and self._symbol.text().strip().upper() != state.active_symbol:
            self._symbol.setText(state.active_symbol)
