from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, List

from .. import config
from ..adapters.base import BaseExchangeAdapter
from ..models import MarketSymbol, SignalEvent
from .base import BaseScanner


class VolumeSpikeScanner(BaseScanner):
    id = "vol_spike"
    name = "Volume Spike"

    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)

    async def scan(self, adapters: Dict[str, BaseExchangeAdapter]) -> List[SignalEvent]:
        signals: List[SignalEvent] = []
        for exchange, adapter in adapters.items():
            symbols = await adapter.list_symbols()
            for raw_symbol in symbols:
                try:
                    candles = await adapter.fetch_ohlcv(raw_symbol, timeframe="1h", limit=49)
                    candles = self._drop_open_candle(candles, timeframe="1h")
                    if len(candles) < 48:
                        continue
                    prev = candles[:24]
                    last = candles[24:]
                    prev_usd = sum(float(c[4]) * float(c[5]) for c in prev)
                    last_usd = sum(float(c[4]) * float(c[5]) for c in last)
                    if prev_usd <= 0:
                        continue
                    ratio = last_usd / prev_usd
                    if last_usd < config.MIN_VOL_USD_LAST or ratio < config.MIN_VOL_RATIO:
                        continue
                    close_ts = int(candles[-1][0])
                    signals.append(
                        SignalEvent(
                            scanner_id=self.id,
                            symbol=MarketSymbol.from_raw(exchange, raw_symbol, market_type="linear_perp"),
                            timeframe="1h",
                            detected_at=datetime.now(timezone.utc),
                            candle_close_at=datetime.fromtimestamp(close_ts / 1000, timezone.utc),
                            score=min(1.0, ratio / 10),
                            metrics={"prev_24h_volume_usd": prev_usd, "last_24h_volume_usd": last_usd, "ratio": ratio},
                        )
                    )
                except Exception:
                    self.logger.exception("failed to process symbol in volume scanner: %s", raw_symbol)
        return signals
