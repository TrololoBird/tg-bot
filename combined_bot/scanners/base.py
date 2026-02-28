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
        units = {"m": 60, "h": 3600, "d": 86400}
        if len(timeframe) < 2:
            raise ValueError(f"unsupported timeframe: {timeframe}")
        unit = timeframe[-1]
        multiplier = units.get(unit)
        if multiplier is None:
            raise ValueError(f"unsupported timeframe: {timeframe}")
        try:
            amount = int(timeframe[:-1])
        except ValueError as exc:
            raise ValueError(f"unsupported timeframe: {timeframe}") from exc
        return amount * multiplier

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
