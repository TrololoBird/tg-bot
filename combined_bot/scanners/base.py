from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, List

from ..adapters.base import BaseExchangeAdapter
from ..models import SignalEvent


class BaseScanner(ABC):
    id = "base"
    name = "Base Scanner"

    @staticmethod
    def _timeframe_seconds(timeframe: str) -> int:
        if timeframe == "1h":
            return 3600
        if timeframe == "1d":
            return 86400
        raise ValueError(f"unsupported timeframe: {timeframe}")

    @classmethod
    def _drop_open_candle(cls, candles: List[List[float]], timeframe: str) -> List[List[float]]:
        if not candles:
            return candles
        duration_seconds = cls._timeframe_seconds(timeframe)
        now_ts = int(datetime.now(timezone.utc).timestamp())
        last_open_ts = int(float(candles[-1][0]) / 1000)
        if now_ts < last_open_ts + duration_seconds:
            return candles[:-1]
        return candles

    @abstractmethod
    async def scan(self, adapters: Dict[str, BaseExchangeAdapter]) -> List[SignalEvent]:
        raise NotImplementedError
