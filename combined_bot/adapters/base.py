from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseExchangeAdapter(ABC):
    exchange_id: str

    @abstractmethod
    async def list_symbols(self) -> List[str]:
        raise NotImplementedError

    @abstractmethod
    async def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int) -> List[List[Any]]:
        raise NotImplementedError

    @abstractmethod
    async def fetch_open_interest_history(self, symbol: str, days: int) -> List[Dict[str, Any]]:
        raise NotImplementedError

    async def close(self) -> None:
        return None
