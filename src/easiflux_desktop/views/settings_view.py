"""API settings and connection configuration view."""

from __future__ import annotations

import asyncio

from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from easiflux_desktop.core.commands import ConnectCommand, SetActiveSymbolCommand, TestConnectionCommand
from easiflux_desktop.core.constants import DEFAULT_BASE_URL
from easiflux_desktop.core.context import AppContext
from easiflux_desktop.models.config import ApiCredential


class SettingsView(QGroupBox):
    def __init__(self, ctx: AppContext, parent=None) -> None:
        super().__init__("设置", parent)
        self._ctx = ctx
        layout = QVBoxLayout(self)
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

    def _load_existing(self) -> None:
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

    def _on_save(self) -> bool:
        cred = self._build_credential()
        account_id = self._ctx.config_manager.config.active_account_id
        try:
            if cred.api_key or cred.api_secret:
                self._ctx.config_manager.set_credentials(account_id, cred)

            config = self._ctx.config_manager.config
            config.active_symbol = self._symbol.text().strip()
            config.use_websocket = self._use_ws.isChecked()
            self._ctx.config_manager.save_config()
            self._ctx.command_bus.execute_background(SetActiveSymbolCommand(config.active_symbol))
            self._status.setText("配置已保存")
            return True
        except Exception as exc:
            self._status.setText(f"保存失败: {exc}")
            QMessageBox.warning(self, "保存失败", str(exc))
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
        if not self._on_save():
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

    def _set_busy(self, busy: bool, label: str | None = None) -> None:
        self._save_btn.setEnabled(not busy)
        self._test_btn.setEnabled(not busy)
        self._connect_btn.setEnabled(not busy)
        if label:
            self._status.setText(label)
