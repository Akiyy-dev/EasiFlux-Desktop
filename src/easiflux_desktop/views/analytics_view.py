"""Analytics dashboard view."""

from __future__ import annotations

import asyncio
from decimal import Decimal, InvalidOperation

from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from easiflux_desktop.core.commands import ExportAnalyticsCommand, ToggleStrategyCommand, UpdateRiskConfigCommand
from easiflux_desktop.core.context import AppContext
from easiflux_desktop.services.risk_manager import RiskConfig


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
        export_row = QHBoxLayout()
        export_btn = QPushButton("导出订单 CSV")
        export_btn.clicked.connect(lambda: asyncio.create_task(self._export_orders()))
        self._export_status = QLabel("导出状态: 未导出")
        export_row.addWidget(export_btn)
        export_row.addWidget(self._export_status)
        stats_layout.addLayout(export_row)
        layout.addWidget(stats_group)

        risk_group = QGroupBox("风险控制")
        risk_layout = QFormLayout(risk_group)
        risk_config = ctx.risk_manager.config
        self._risk_enabled = QCheckBox("启用风控")
        self._risk_enabled.setChecked(risk_config.enabled)
        self._max_qty = QLineEdit(str(risk_config.max_order_qty))
        self._max_price_deviation = QLineEdit(str(risk_config.max_price_deviation_pct))
        self._max_daily_orders = QLineEdit(str(risk_config.max_daily_orders))
        save_risk_btn = QPushButton("保存风控")
        save_risk_btn.clicked.connect(lambda: asyncio.create_task(self._save_risk_config()))
        self._risk_status = QLabel("风控状态: 未修改")
        risk_layout.addRow("", self._risk_enabled)
        risk_layout.addRow("最大单笔数量", self._max_qty)
        risk_layout.addRow("最大价格偏离%", self._max_price_deviation)
        risk_layout.addRow("每日订单上限", self._max_daily_orders)
        risk_layout.addRow(save_risk_btn, self._risk_status)
        layout.addWidget(risk_group)

        strategy_group = QGroupBox("策略")
        self._strategy_layout = QVBoxLayout(strategy_group)
        self._strategy_rows: dict[str, tuple[QLabel, QPushButton]] = {}
        self._render_strategies()
        layout.addWidget(strategy_group)
        layout.addStretch()

        ctx.event_bus.subscribe("order.updated", lambda _: self._refresh())
        ctx.event_bus.subscribe("position.updated", lambda _: self._refresh())
        ctx.event_bus.subscribe("strategy.states_updated", lambda _: self._render_strategies())
        ctx.event_bus.subscribe("risk.config_updated", self._on_risk_config_updated)
        self._refresh()

    def _refresh(self) -> None:
        stats = self._ctx.analytics_service.compute_stats()
        self._total_orders.setText(f"总订单: {stats.total_orders}")
        self._filled_orders.setText(f"成交: {stats.filled_orders}")
        self._pnl.setText(f"未实现盈亏: {stats.total_pnl}")
        self._win_loss.setText(f"盈/亏仓位: {stats.win_count} / {stats.loss_count}")

    async def _export_orders(self) -> None:
        self._export_status.setText("导出状态: 导出中...")
        result = await self._ctx.command_bus.execute(ExportAnalyticsCommand())
        if result.success:
            self._export_status.setText(f"导出状态: {result.data}")
        elif result.error:
            self._export_status.setText(f"导出失败: {result.error.user_message}")

    async def _save_risk_config(self) -> None:
        risk_config = self._build_risk_config()
        if risk_config is None:
            return
        self._risk_status.setText("风控状态: 保存中...")
        result = await self._ctx.command_bus.execute(UpdateRiskConfigCommand(risk_config))
        if result.success:
            self._risk_status.setText("风控状态: 已保存")
        elif result.error:
            self._risk_status.setText(f"风控保存失败: {result.error.user_message}")

    def _build_risk_config(self) -> RiskConfig | None:
        try:
            max_qty = Decimal(self._max_qty.text().strip())
            max_deviation = Decimal(self._max_price_deviation.text().strip())
            max_daily_orders = int(self._max_daily_orders.text().strip())
        except (InvalidOperation, ValueError):
            self._risk_status.setText("风控保存失败: 参数格式无效")
            return None

        if max_qty <= 0 or max_deviation < 0 or max_daily_orders <= 0:
            self._risk_status.setText("风控保存失败: 参数必须为正数")
            return None

        return RiskConfig(
            max_order_qty=max_qty,
            max_price_deviation_pct=max_deviation,
            max_daily_orders=max_daily_orders,
            enabled=self._risk_enabled.isChecked(),
        )

    def _on_risk_config_updated(self, risk_config: RiskConfig) -> None:
        self._risk_enabled.setChecked(risk_config.enabled)
        self._max_qty.setText(str(risk_config.max_order_qty))
        self._max_price_deviation.setText(str(risk_config.max_price_deviation_pct))
        self._max_daily_orders.setText(str(risk_config.max_daily_orders))

    def _render_strategies(self) -> None:
        for state in self._ctx.strategy_manager.list_strategies():
            row = self._strategy_rows.get(state.name)
            label_text = f"{state.name}: {'启用' if state.enabled else '禁用'}"
            button_text = "停用" if state.enabled else "启用"
            if row is None:
                label = QLabel(label_text)
                button = QPushButton(button_text)
                button.clicked.connect(
                    lambda _=False, name=state.name: asyncio.create_task(self._toggle_strategy(name))
                )
                row_layout = QHBoxLayout()
                row_layout.addWidget(label)
                row_layout.addWidget(button)
                self._strategy_layout.addLayout(row_layout)
                self._strategy_rows[state.name] = (label, button)
            else:
                label, button = row
                label.setText(label_text)
                button.setText(button_text)

    async def _toggle_strategy(self, name: str) -> None:
        current = next((state for state in self._ctx.strategy_manager.list_strategies() if state.name == name), None)
        if current is None:
            return
        result = await self._ctx.command_bus.execute(ToggleStrategyCommand(name, not current.enabled))
        if result.success:
            self._render_strategies()
