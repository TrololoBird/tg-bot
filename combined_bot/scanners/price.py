from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, List

from .. import config
from ..adapters.base import BaseExchangeAdapter
from ..models import MarketSymbol, SignalEvent
from .base import BaseScanner


class PricePumpScanner(BaseScanner):
    id = "price_pump"
    name = "24h Price Pump"

    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)

    async def scan(self, adapters: Dict[str, BaseExchangeAdapter]) -> List[SignalEvent]:
        signals: List[SignalEvent] = []
        for exchange, adapter in adapters.items():
            symbols = await adapter.list_symbols()
            for raw_symbol in symbols:
                try:
                    candles = await adapter.fetch_ohlcv(raw_symbol, timeframe="1h", limit=25)
                    candles = self._drop_open_candle(candles, timeframe="1h")
                    if len(candles) < 24:
                        continue
                    first_close = float(candles[0][4])
                    last_close = float(candles[-1][4])
                    if first_close <= 0:
                        continue
                    ratio = last_close / first_close
                    usd_volume = sum(float(c[4]) * float(c[5]) for c in candles)
                    if ratio < config.MIN_PRICE_RATIO or usd_volume < config.MIN_PRICE_SCANNER_VOL_USD_24H:
                        continue
                    close_ts = int(candles[-1][0])
                    signals.append(
                        SignalEvent(
                            scanner_id=self.id,
                            symbol=MarketSymbol.from_raw(exchange, raw_symbol, market_type="linear_perp"),
                            timeframe="1h",
                            detected_at=datetime.now(timezone.utc),
                            candle_close_at=datetime.fromtimestamp(close_ts / 1000, timezone.utc),
                            direction="LONG",
                            score=min(1.0, (ratio - 1.0) / max(config.PRICE_SCORE_MAX_RATIO - 1.0, 1e-9)),
                            metrics={"price_ratio": ratio, "volume_usd": usd_volume},
                        )
                    )
                except Exception:
                    self.logger.exception("failed to process symbol in price scanner: %s", raw_symbol)
        return signals
