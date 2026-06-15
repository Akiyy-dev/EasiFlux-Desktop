"""Local in-memory and file cache for market data."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from easiflux_desktop.models.market import DesktopKline, DesktopTicker


@dataclass
class CacheKey:
    symbol: str
    interval: str = ""


@dataclass
class CacheStore:
    tickers: dict[str, DesktopTicker] = field(default_factory=dict)
    klines: dict[tuple[str, str], list[DesktopKline]] = field(default_factory=lambda: defaultdict(list))
    recent_symbols: list[str] = field(default_factory=list)

    def set_ticker(self, ticker: DesktopTicker) -> None:
        self.tickers[ticker.symbol] = ticker
        self._touch_symbol(ticker.symbol)

    def get_ticker(self, symbol: str) -> DesktopTicker | None:
        return self.tickers.get(symbol)

    def set_klines(self, symbol: str, interval: str, klines: list[DesktopKline]) -> None:
        self.klines[(symbol, interval)] = klines
        self._touch_symbol(symbol)

    def get_klines(self, symbol: str, interval: str) -> list[DesktopKline]:
        return list(self.klines.get((symbol, interval), []))

    def _touch_symbol(self, symbol: str) -> None:
        if symbol in self.recent_symbols:
            self.recent_symbols.remove(symbol)
        self.recent_symbols.insert(0, symbol)
        self.recent_symbols = self.recent_symbols[:20]
