"""Order placement panel widget."""

from __future__ import annotations

import asyncio
from decimal import Decimal, InvalidOperation

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

from easiflux_desktop.core.commands import PlaceOrderCommand
from easiflux_desktop.core.context import AppContext
from easiflux_desktop.core.state_store import MarketState
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
        ctx.event_bus.subscribe("state.market.updated", self._on_market_state)

    def _on_submit(self) -> None:
        if self._busy:
            return
        request = PlaceOrderRequest(
            symbol=self._symbol.text().strip(),
            side=self._side.currentText(),
            order_type=self._type.currentText(),
            price=self._price.text().strip() or None,
            qty=self._qty.text().strip(),
        )
        validation_error = self._validate_order_input(request)
        if validation_error:
            self._status.setText(validation_error)
            return
        if not self._confirm_order(request):
            self._status.setText("已取消下单")
            return
        self._set_busy(True)
        self._status.setText("提交订单中...")
        asyncio.create_task(self._place_order(request))

    async def _place_order(self, request: PlaceOrderRequest) -> None:
        try:
            result = await self._ctx.command_bus.execute(PlaceOrderCommand(request))
            if result.success:
                self._status.setText(f"订单已提交: {result.data.order_id}")
            elif result.error:
                self._status.setText(result.error.user_message)
        except Exception as exc:
            self._status.setText(str(exc))
        finally:
            self._set_busy(False)

    def _validate_order_input(self, request: PlaceOrderRequest) -> str | None:
        if not request.symbol:
            return "交易对不能为空"
        if not request.qty:
            return "数量不能为空"
        try:
            qty = Decimal(request.qty)
        except InvalidOperation:
            return "数量格式无效"
        if qty <= 0:
            return "数量必须大于 0"

        if request.order_type.lower() == "limit":
            if not request.price:
                return "限价单必须填写价格"
            try:
                price = Decimal(request.price)
            except InvalidOperation:
                return "价格格式无效"
            if price <= 0:
                return "价格必须大于 0"
        return None

    def _confirm_order(self, request: PlaceOrderRequest) -> bool:
        price = request.price if request.order_type.lower() == "limit" else "市价"
        message = (
            f"交易对: {request.symbol}\n"
            f"方向: {request.side}\n"
            f"类型: {request.order_type}\n"
            f"价格: {price}\n"
            f"数量: {request.qty}\n\n确认提交订单？"
        )
        return (
            QMessageBox.question(
                self,
                "确认下单",
                message,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            == QMessageBox.StandardButton.Yes
        )

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        self._submit_btn.setEnabled(not busy)
        self._submit_btn.setText("提交中..." if busy else "下单")

    def _on_order_created(self, order) -> None:
        self._status.setText(f"订单 {order.order_id} 状态: {order.status_display}")

    def _on_market_state(self, state: MarketState) -> None:
        if not self._symbol.hasFocus() and self._symbol.text().strip().upper() != state.active_symbol:
            self._symbol.setText(state.active_symbol)
