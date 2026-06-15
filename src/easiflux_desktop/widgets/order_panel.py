"""Order placement panel widget."""

from __future__ import annotations

import asyncio

from PySide6.QtWidgets import (
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

from easiflux_desktop.core.context import AppContext
from easiflux_desktop.models.trading import PlaceOrderRequest


class OrderPanel(QGroupBox):
    def __init__(self, ctx: AppContext, parent=None) -> None:
        super().__init__("下单", parent)
        self._ctx = ctx
        self._busy = False

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._symbol = QLineEdit(ctx.config_manager.config.active_symbol)
        self._side = QComboBox()
        self._side.addItems(["Buy", "Sell"])
        self._type = QComboBox()
        self._type.addItems(["Limit", "Market"])
        self._price = QLineEdit()
        self._price.setPlaceholderText("限价单必填")
        self._qty = QLineEdit("0.001")

        form.addRow("交易对", self._symbol)
        form.addRow("方向", self._side)
        form.addRow("类型", self._type)
        form.addRow("价格", self._price)
        form.addRow("数量", self._qty)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        self._submit_btn = QPushButton("下单")
        self._submit_btn.clicked.connect(self._on_submit)
        btn_row.addWidget(self._submit_btn)
        layout.addLayout(btn_row)

        self._status = QLabel("")
        layout.addWidget(self._status)

        ctx.event_bus.subscribe("order.created", self._on_order_created)
        ctx.event_bus.subscribe("error.occurred", self._on_error)

    def _on_submit(self) -> None:
        if self._busy:
            return
        self._busy = True
        self._submit_btn.setEnabled(False)
        request = PlaceOrderRequest(
            symbol=self._symbol.text().strip(),
            side=self._side.currentText(),
            order_type=self._type.currentText(),
            price=self._price.text().strip() or None,
            qty=self._qty.text().strip(),
        )
        asyncio.create_task(self._place_order(request))

    async def _place_order(self, request: PlaceOrderRequest) -> None:
        try:
            order = await self._ctx.trading_manager.place_order(request)
            self._status.setText(f"订单已提交: {order.order_id}")
        except Exception as exc:
            self._status.setText(str(exc))
        finally:
            self._busy = False
            self._submit_btn.setEnabled(True)

    def _on_order_created(self, order) -> None:
        self._status.setText(f"订单 {order.order_id} 状态: {order.status_display}")

    def _on_error(self, error) -> None:
        QMessageBox.warning(self, "错误", error.user_message)
