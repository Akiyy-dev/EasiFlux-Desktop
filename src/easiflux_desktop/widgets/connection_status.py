"""Connection status indicator widget."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel

from easiflux_desktop.core.context import AppContext
from easiflux_desktop.models.config import ConnectionStatus


class ConnectionStatusWidget(QLabel):
    def __init__(self, ctx: AppContext, parent=None) -> None:
        super().__init__(parent)
        self._ctx = ctx
        self.setText("未连接")
        self._on_status(ctx.state_store.account.connection_status)
        ctx.event_bus.subscribe("state.connection.updated", self._on_status)

    def _on_status(self, status: ConnectionStatus) -> None:
        labels = {
            ConnectionStatus.DISCONNECTED: "未连接",
            ConnectionStatus.CONNECTING: "连接中...",
            ConnectionStatus.CONNECTED: "已连接",
            ConnectionStatus.ERROR: "连接错误",
        }
        self.setText(labels.get(status, "未知"))
        self._apply_style(status)

    def _apply_style(self, status: ConnectionStatus) -> None:
        colors = {
            ConnectionStatus.DISCONNECTED: "#9e9e9e",
            ConnectionStatus.CONNECTING: "#ffb74d",
            ConnectionStatus.CONNECTED: "#26a69a",
            ConnectionStatus.ERROR: "#ef5350",
        }
        color = colors.get(status, "#9e9e9e")
        self.setStyleSheet(f"color: {color}; font-weight: bold; padding: 4px 8px;")
