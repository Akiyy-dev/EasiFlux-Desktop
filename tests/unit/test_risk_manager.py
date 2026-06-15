"""Unit tests for risk manager."""

from decimal import Decimal

import pytest

from easiflux_desktop.core.errors import RiskError
from easiflux_desktop.models.trading import PlaceOrderRequest
from easiflux_desktop.services.risk_manager import RiskConfig, RiskManager


@pytest.mark.asyncio
async def test_max_qty_rejected():
    risk = RiskManager(RiskConfig(max_order_qty=Decimal("1")))
    request = PlaceOrderRequest(symbol="BTCUSDT", side="Buy", order_type="Market", qty="10")
    with pytest.raises(RiskError):
        await risk.validate_order(request)


@pytest.mark.asyncio
async def test_valid_order_passes():
    risk = RiskManager(RiskConfig(max_order_qty=Decimal("100")))
    request = PlaceOrderRequest(symbol="BTCUSDT", side="Buy", order_type="Market", qty="0.01")
    await risk.validate_order(request)
