"""Open orders table widget."""

from __future__ import annotations

import asyncio

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from easiflux_desktop.core.commands import CancelOrderCommand, RefreshOrdersCommand
from easiflux_desktop.core.context import AppContext
from easiflux_desktop.core.state_store import OrderState
from easiflux_desktop.models.trading import DesktopOrder


class OrderTable(QGroupBox):
    HEADERS = ["订单ID", "交易对", "方向", "类型", "价格", "数量", "状态", "操作"]

    def __init__(self, ctx: AppContext, parent=None) -> None:
        super().__init__("订单", parent)
        self._ctx = ctx
        self._busy = False
        layout = QVBoxLayout(self)

        btn_row = QHBoxLayout()
        self._refresh_btn = QPushButton("刷新")
        self._refresh_btn.clicked.connect(lambda: asyncio.create_task(self._refresh()))
        btn_row.addWidget(self._refresh_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self._status = QLabel("订单状态: 未刷新")
        layout.addWidget(self._status)

        self._table = QTableWidget(0, len(self.HEADERS))
        self._table.setHorizontalHeaderLabels(self.HEADERS)
        self._table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self._table)

        ctx.event_bus.subscribe("state.orders.updated", self._on_order_state)
        self.set_orders(ctx.state_store.orders.open_orders())

    async def _refresh(self) -> None:
        if self._busy:
            return
        self._set_busy(True, "订单状态: 刷新中...")
        try:
            result = await self._ctx.command_bus.execute(RefreshOrdersCommand())
            if result.success:
                self._status.setText("订单状态: 已刷新")
            elif result.error:
                self._status.setText(f"订单状态: 刷新失败 - {result.error.user_message}")
        finally:
            self._set_busy(False)

    def set_orders(self, orders: list[DesktopOrder]) -> None:
        self._table.setRowCount(len(orders))
        for row, order in enumerate(orders):
            values = [
                order.order_id,
                order.symbol,
                order.side,
                order.order_type,
                str(order.price),
                str(order.qty),
                order.status_display,
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                if col == 2:
                    item.setForeground(QColor(order.side_color))
                self._table.setItem(row, col, item)

            if not order.is_terminal:
                cancel_btn = QPushButton("撤单")
                oid = order.order_id
                sym = order.symbol
                cancel_btn.clicked.connect(
                    lambda _=False, s=sym, o=oid: asyncio.create_task(self._cancel(s, o))
                )
                self._table.setCellWidget(row, 7, cancel_btn)
            else:
                self._table.removeCellWidget(row, 7)
                self._table.setItem(row, 7, QTableWidgetItem("—"))

    async def _cancel(self, symbol: str, order_id: str) -> None:
        if self._busy:
            return
        if QMessageBox.question(
            self,
            "确认撤单",
            f"确认撤销订单 {order_id}？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        ) != QMessageBox.StandardButton.Yes:
            self._status.setText("订单状态: 已取消撤单")
            return

        self._set_busy(True, f"订单状态: 正在撤销 {order_id}...")
        try:
            result = await self._ctx.command_bus.execute(CancelOrderCommand(symbol, order_id))
            if result.success:
                self._status.setText(f"订单状态: 已撤单 {order_id}")
            elif result.error:
                self._status.setText(f"订单状态: 撤单失败 - {result.error.user_message}")
        finally:
            self._set_busy(False)

    def _on_order_state(self, state: OrderState) -> None:
        self.set_orders(state.open_orders())

    def _set_busy(self, busy: bool, status: str | None = None) -> None:
        self._busy = busy
        self._refresh_btn.setEnabled(not busy)
        if status:
            self._status.setText(status)
