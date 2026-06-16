"""Trading operations with basic risk validation."""

from __future__ import annotations

import logging
from decimal import Decimal, InvalidOperation

from easiflux_desktop.adapters.rest_adapter import RestAdapter
from easiflux_desktop.adapters.ws_adapter import WsAdapter
from easiflux_desktop.core.errors import ValidationError
from easiflux_desktop.core.event_bus import EventBus
from easiflux_desktop.models.trading import DesktopOrder, PlaceOrderRequest
from easiflux_desktop.services.risk_manager import RiskManager

logger = logging.getLogger(__name__)


class TradingManager:
    def __init__(
        self,
        rest: RestAdapter,
        ws: WsAdapter,
        risk: RiskManager,
        event_bus: EventBus,
    ) -> None:
        self._rest = rest
        self._ws = ws
        self._risk = risk
        self._event_bus = event_bus
        self._orders: dict[str, DesktopOrder] = {}

    def validate_order(self, request: PlaceOrderRequest) -> None:
        if not request.symbol:
            raise ValidationError("交易对不能为空")
        if not request.qty:
            raise ValidationError("数量不能为空")

        try:
            qty = Decimal(request.qty)
        except InvalidOperation as exc:
            raise ValidationError("数量格式无效") from exc

        if qty <= 0:
            raise ValidationError("数量必须大于 0")

        if request.order_type.lower() == "limit":
            if not request.price:
                raise ValidationError("限价单必须填写价格")
            try:
                price = Decimal(request.price)
            except InvalidOperation as exc:
                raise ValidationError("价格格式无效") from exc
            if price <= 0:
                raise ValidationError("价格必须大于 0")

    async def place_order(self, request: PlaceOrderRequest) -> DesktopOrder:
        self.validate_order(request)
        await self._risk.validate_order(request)
        order = await self._rest.create_order(request)
        self._orders[order.order_id] = order
        self._event_bus.publish("order.created", order)
        logger.info("Order placed: %s %s %s", order.order_id, order.symbol, order.side)
        return order

    async def cancel_order(self, symbol: str, order_id: str) -> DesktopOrder:
        order = await self._rest.cancel_order(symbol, order_id)
        self._orders[order.order_id] = order
        self._event_bus.publish("order.updated", order)
        return order

    async def get_open_orders(self, symbol: str | None = None) -> list[DesktopOrder]:
        orders = await self._rest.get_open_orders(symbol)
        for order in orders:
            self._orders[order.order_id] = order
        self._event_bus.publish("orders.loaded", {"symbol": symbol, "orders": orders})
        return orders

    async def refresh_orders(self, symbol: str | None = None) -> list[DesktopOrder]:
        return await self.get_open_orders(symbol)

    async def subscribe_order_updates(self) -> None:
        await self._ws.subscribe_orders()
