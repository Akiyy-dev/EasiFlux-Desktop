"""Analytics dashboard view."""

from __future__ import annotations

from PySide6.QtWidgets import QGroupBox, QLabel, QVBoxLayout, QWidget

from easiflux_desktop.core.context import AppContext


class AnalyticsView(QWidget):
    def __init__(self, ctx: AppContext, parent=None) -> None:
        super().__init__(parent)
        self._ctx = ctx
        layout = QVBoxLayout(self)

        stats_group = QGroupBox("交易统计")
        stats_layout = QVBoxLayout(stats_group)
        self._total_orders = QLabel("总订单: 0")
        self._filled_orders = QLabel("成交: 0")
        self._pnl = QLabel("未实现盈亏: 0")
        self._win_loss = QLabel("盈/亏仓位: 0 / 0")
        for label in (self._total_orders, self._filled_orders, self._pnl, self._win_loss):
            stats_layout.addWidget(label)
        layout.addWidget(stats_group)

        strategy_group = QGroupBox("策略")
        strategy_layout = QVBoxLayout(strategy_group)
        strategies = ctx.strategy_manager.list_strategies()
        for state in strategies:
            strategy_layout.addWidget(QLabel(f"{state.name}: {'启用' if state.enabled else '禁用'}"))
        layout.addWidget(strategy_group)
        layout.addStretch()

        ctx.event_bus.subscribe("order.updated", lambda _: self._refresh())
        ctx.event_bus.subscribe("position.updated", lambda _: self._refresh())
        self._refresh()

    def _refresh(self) -> None:
        stats = self._ctx.analytics_service.compute_stats()
        self._total_orders.setText(f"总订单: {stats.total_orders}")
        self._filled_orders.setText(f"成交: {stats.filled_orders}")
        self._pnl.setText(f"未实现盈亏: {stats.total_pnl}")
        self._win_loss.setText(f"盈/亏仓位: {stats.win_count} / {stats.loss_count}")
