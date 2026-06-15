"""Open orders table widget."""

from __future__ import annotations

import asyncio

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from easiflux_desktop.core.context import AppContext
from easiflux_desktop.models.trading import DesktopOrder


class OrderTable(QGroupBox):
    HEADERS = ["订单ID", "交易对", "方向", "类型", "价格", "数量", "状态", "操作"]

    def __init__(self, ctx: AppContext, parent=None) -> None:
        super().__init__("订单", parent)
        self._ctx = ctx
        layout = QVBoxLayout(self)

        btn_row = QHBoxLayout()
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(lambda: asyncio.create_task(self._refresh()))
        btn_row.addWidget(refresh_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self._table = QTableWidget(0, len(self.HEADERS))
        self._table.setHorizontalHeaderLabels(self.HEADERS)
        self._table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self._table)

        ctx.event_bus.subscribe("order.created", self._on_order_event)
        ctx.event_bus.subscribe("order.updated", self._on_order_event)

    async def _refresh(self) -> None:
        orders = await self._ctx.trading_manager.refresh_orders()
        self.set_orders(orders)

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

    async def _cancel(self, symbol: str, order_id: str) -> None:
        await self._ctx.trading_manager.cancel_order(symbol, order_id)
        await self._refresh()

    def _on_order_event(self, order: DesktopOrder) -> None:
        asyncio.create_task(self._refresh())
