from __future__ import annotations

from typing import Any, Dict, List

from .base import BaseExchangeAdapter


class BinanceFuturesAdapter(BaseExchangeAdapter):
    exchange_id = "binance"

    async def list_symbols(self) -> List[str]:
        return []

    async def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int) -> List[List[Any]]:
        return []

    async def fetch_open_interest_history(self, symbol: str, days: int) -> List[Dict[str, Any]]:
        return []
