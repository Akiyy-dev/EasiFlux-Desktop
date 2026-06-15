"""REST API adapter wrapping AsyncEasiFluxSDK."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from easiflux_sdk import AuthenticationError as SdkAuthError
from easiflux_sdk import CancelOrderRequest, RateLimitError, SDKError
from easiflux_sdk.config import DEFAULT_ENDPOINTS
from easiflux_sdk.core.operations import (
    build_cancel_order_payload,
    build_depth_params,
    build_kline_params,
    build_order_query_params,
)

from easiflux_desktop.adapters.model_mapper import ModelMapper, extract_list
from easiflux_desktop.adapters.sdk_client_factory import SdkClientFactory
from easiflux_desktop.core.errors import AuthenticationError, ConnectionError, TradingError
from easiflux_desktop.models.account import DesktopBalance
from easiflux_desktop.models.market import DesktopDepth, DesktopKline, DesktopTicker
from easiflux_desktop.models.trading import DesktopOrder, DesktopPosition, OrderStatus, PlaceOrderRequest

logger = logging.getLogger(__name__)


class RestAdapter:
    def __init__(self, factory: SdkClientFactory) -> None:
        self._factory = factory

    def _map_error(self, exc: Exception) -> Exception:
        if isinstance(exc, SdkAuthError):
            return AuthenticationError("API 认证失败，请检查 Key 和 Secret", cause=exc)
        if isinstance(exc, RateLimitError):
            return ConnectionError("请求频率超限，请稍后重试", cause=exc)
        if isinstance(exc, SDKError):
            return TradingError(str(exc), cause=exc)
        return ConnectionError(str(exc), cause=exc)

    async def _call(self, coro: Any) -> Any:
        try:
            return await coro
        except Exception as exc:
            raise self._map_error(exc) from exc

    async def get_server_time(self) -> Any:
        client = self._factory.require_client()
        return await self._call(client.get_server_time())

    async def get_ticker(self, symbol: str) -> DesktopTicker:
        client = self._factory.require_client()
        payload = await self._call(client.get_ticker(symbol=symbol))
        items = extract_list(payload)
        if items:
            ticker = ModelMapper.to_desktop_ticker(items[0], symbol=symbol)
        else:
            data = payload if isinstance(payload, dict) else {}
            ticker = ModelMapper.to_desktop_ticker(data, symbol=symbol)
        if not ticker.symbol:
            ticker.symbol = symbol
        return ticker

    async def get_klines(self, symbol: str, interval: str, *, limit: int = 200) -> list[DesktopKline]:
        client = self._factory.require_client()
        params = build_kline_params(symbol=symbol, interval=interval, limit=limit)
        path = DEFAULT_ENDPOINTS["kline"]
        payload = await self._call(client.public_request("GET", path, params=params))
        return ModelMapper.klines_from_payload(payload, symbol, interval)

    async def get_depth(self, symbol: str, *, limit: int = 20) -> DesktopDepth:
        client = self._factory.require_client()
        params = build_depth_params(symbol=symbol, limit=limit)
        path = DEFAULT_ENDPOINTS["depth"]
        payload = await self._call(client.public_request("GET", path, params=params))
        return ModelMapper.depth_from_payload(payload, symbol)

    async def create_order(self, request: PlaceOrderRequest) -> DesktopOrder:
        client = self._factory.require_client()
        sdk_request = ModelMapper.to_sdk_order_request(request)
        payload = await self._call(client.create_order(sdk_request))
        items = extract_list(payload)
        if items:
            return ModelMapper.to_desktop_order(items[0])
        if isinstance(payload, dict):
            return ModelMapper.to_desktop_order(payload)
        return DesktopOrder(
            order_id="",
            symbol=request.symbol,
            side=request.side,
            order_type=request.order_type,
            price=Decimal(request.price or "0"),
            qty=Decimal(request.qty),
            status=OrderStatus.NEW,
        )

    async def cancel_order(self, symbol: str, order_id: str) -> DesktopOrder:
        client = self._factory.require_client()
        cancel = CancelOrderRequest(symbol=symbol, order_id=order_id)
        payload = build_cancel_order_payload(cancel)
        path = DEFAULT_ENDPOINTS["cancel_order"]
        result = await self._call(client.private_request("POST", path, json_body=payload))
        items = extract_list(result)
        if items:
            return ModelMapper.to_desktop_order(items[0])
        fallback = {"order_id": order_id, "symbol": symbol, "status": "Cancelled"}
        raw = result if isinstance(result, dict) else fallback
        return ModelMapper.to_desktop_order(raw)

    async def get_open_orders(self, symbol: str | None = None) -> list[DesktopOrder]:
        client = self._factory.require_client()
        params = build_order_query_params(symbol=symbol)
        path = DEFAULT_ENDPOINTS["order"]
        payload = await self._call(client.private_request("GET", path, params=params))
        return ModelMapper.orders_from_payload(payload)

    async def get_balances(self) -> list[DesktopBalance]:
        client = self._factory.require_client()
        payload = await self._call(client.get_balances())
        return ModelMapper.balances_from_payload(payload)

    async def get_positions(self, symbol: str | None = None) -> list[DesktopPosition]:
        client = self._factory.require_client()
        params = build_order_query_params(symbol=symbol)
        path = DEFAULT_ENDPOINTS["positions"]
        payload = await self._call(client.private_request("GET", path, params=params))
        return ModelMapper.positions_from_payload(payload)
