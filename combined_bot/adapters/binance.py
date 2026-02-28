from __future__ import annotations

from typing import Any, Dict, List

import ccxt.async_support as ccxt

from .base import BaseExchangeAdapter


class BinanceFuturesAdapter(BaseExchangeAdapter):
    exchange_id = "binance"

    def __init__(self) -> None:
        self._client = ccxt.binanceusdm({"enableRateLimit": True})
        self._markets_loaded = False

    async def _ensure_markets_loaded(self) -> None:
        if not self._markets_loaded:
            await self._client.load_markets()
            self._markets_loaded = True

    async def list_symbols(self) -> List[str]:
        await self._ensure_markets_loaded()
        symbols: List[str] = []
        for market in self._client.markets.values():
            if market.get("active") and market.get("swap") and market.get("linear") and market.get("quote") == "USDT":
                symbols.append(str(market["symbol"]))
        return symbols

    async def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int) -> List[List[Any]]:
        await self._ensure_markets_loaded()
        return await self._client.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

    async def fetch_open_interest_history(self, symbol: str, days: int) -> List[Dict[str, Any]]:
        await self._ensure_markets_loaded()
        history = await self._client.fetch_open_interest_history(symbol, timeframe="1d", limit=days)
        return [{"ts": item.get("timestamp", 0), "oi": item.get("openInterestAmount", 0)} for item in history]

    async def close(self) -> None:
        await self._client.close()
