"""Trading view with order panel and order table."""

from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from easiflux_desktop.core.context import AppContext
from easiflux_desktop.widgets.order_panel import OrderPanel
from easiflux_desktop.widgets.order_table import OrderTable


class TradingView(QWidget):
    def __init__(self, ctx: AppContext, parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        left = QVBoxLayout()
        left.addWidget(OrderPanel(ctx))
        left.addStretch()
        layout.addLayout(left, 1)
        layout.addWidget(OrderTable(ctx), 2)
