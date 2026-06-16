"""Position table widget."""

from __future__ import annotations

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGroupBox, QTableWidget, QTableWidgetItem, QVBoxLayout

from easiflux_desktop.core.context import AppContext
from easiflux_desktop.core.state_store import PositionState
from easiflux_desktop.models.trading import DesktopPosition


class PositionTable(QGroupBox):
    HEADERS = ["交易对", "方向", "数量", "开仓价", "杠杆", "未实现盈亏", "收益率%"]

    def __init__(self, ctx: AppContext, parent=None) -> None:
        super().__init__("持仓", parent)
        self._ctx = ctx
        layout = QVBoxLayout(self)
        self._table = QTableWidget(0, len(self.HEADERS))
        self._table.setHorizontalHeaderLabels(self.HEADERS)
        self._table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self._table)
        ctx.event_bus.subscribe("state.positions.updated", self._on_position_state)
        self.set_positions(ctx.state_store.positions.position_list())

    def set_positions(self, positions: list[DesktopPosition]) -> None:
        self._table.setRowCount(len(positions))
        for row, pos in enumerate(positions):
            values = [
                pos.symbol,
                pos.side.value,
                pos.size_display,
                str(pos.entry_price),
                str(pos.leverage),
                str(pos.unrealised_pnl),
                f"{pos.pnl_pct:.2f}",
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                if col == 5:
                    item.setForeground(QColor(pos.pnl_color))
                self._table.setItem(row, col, item)

    def _on_position_state(self, state: PositionState) -> None:
        self.set_positions(state.position_list())
