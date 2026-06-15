"""Basic risk validation before order placement."""

from __future__ import annotations

from decimal import Decimal

from easiflux_desktop.core.errors import RiskError
from easiflux_desktop.models.trading import PlaceOrderRequest


class RiskConfig:
    def __init__(
        self,
        *,
        max_order_qty: Decimal = Decimal("100"),
        max_price_deviation_pct: Decimal = Decimal("5"),
        max_daily_orders: int = 500,
        enabled: bool = True,
    ) -> None:
        self.max_order_qty = max_order_qty
        self.max_price_deviation_pct = max_price_deviation_pct
        self.max_daily_orders = max_daily_orders
        self.enabled = enabled


class RiskManager:
    def __init__(self, config: RiskConfig | None = None) -> None:
        self._config = config or RiskConfig()
        self._daily_order_count = 0

    @property
    def config(self) -> RiskConfig:
        return self._config

    def update_config(self, config: RiskConfig) -> None:
        self._config = config

    async def validate_order(self, request: PlaceOrderRequest, reference_price: Decimal | None = None) -> None:
        if not self._config.enabled:
            return

        qty = Decimal(request.qty)
        if qty > self._config.max_order_qty:
            raise RiskError(f"订单数量 {qty} 超过最大限制 {self._config.max_order_qty}")

        if self._daily_order_count >= self._config.max_daily_orders:
            raise RiskError(f"今日下单次数已达上限 {self._config.max_daily_orders}")

        if request.order_type.lower() == "limit" and request.price and reference_price:
            price = Decimal(request.price)
            if reference_price > 0:
                deviation = abs(price - reference_price) / reference_price * 100
                if deviation > self._config.max_price_deviation_pct:
                    raise RiskError(
                        f"限价偏离市价 {deviation:.2f}%，超过限制 {self._config.max_price_deviation_pct}%"
                    )

        self._daily_order_count += 1

    def reset_daily_count(self) -> None:
        self._daily_order_count = 0
