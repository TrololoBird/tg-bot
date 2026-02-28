from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List

from .. import config
from ..adapters.base import BaseExchangeAdapter
from ..models import MarketSymbol, SignalEvent
from .base import BaseScanner


class OpenInterestScanner(BaseScanner):
    id = "oi_spike"
    name = "Open Interest Spike"

    def _sort_value(self, oi_end: float, avg_daily_vol_usd: float, price_growth_pct: float, end_close: float) -> float:
        mode = config.OI_SORT_BY
        if mode == "oi_contracts":
            return oi_end
        if mode == "price_growth":
            return price_growth_pct
        if mode == "avg_daily_vol_usd":
            return avg_daily_vol_usd
        return oi_end * end_close

    def _drop_open_oi_point(self, oi_hist: List[Dict[str, float]]) -> List[Dict[str, float]]:
        if not oi_hist:
            return oi_hist
        now_ts = int(datetime.now(timezone.utc).timestamp())
        last_ts = int(float(oi_hist[-1].get("ts", 0)) / 1000)
        if now_ts < last_ts + self._timeframe_seconds("1d"):
            return oi_hist[:-1]
        return oi_hist

    async def scan(self, adapters: Dict[str, BaseExchangeAdapter]) -> List[SignalEvent]:
        signals_with_sort: List[tuple[float, SignalEvent]] = []
        for exchange, adapter in adapters.items():
            symbols = await adapter.list_symbols()
            for raw_symbol in symbols:
                oi_hist = await adapter.fetch_open_interest_history(raw_symbol, days=config.OI_DAYS + 1)
                oi_hist = self._drop_open_oi_point(oi_hist)
                candles = await adapter.fetch_ohlcv(raw_symbol, timeframe="1d", limit=config.OI_DAYS + 2)
                candles = self._drop_open_candle(candles, timeframe="1d")

                window_size = min(config.OI_DAYS, len(oi_hist), len(candles))
                if window_size < 2:
                    continue
                aligned_oi = oi_hist[-window_size:]
                aligned_candles = candles[-window_size:]

                start = float(aligned_oi[0].get("oi", 0.0))
                end = float(aligned_oi[-1].get("oi", 0.0))
                if start <= 0:
                    continue
                growth_pct = (end - start) / start * 100
                if growth_pct < config.OI_GROWTH_PCT:
                    continue

                start_close = float(aligned_candles[0][4])
                end_close = float(aligned_candles[-1][4])
                if start_close <= 0:
                    continue

                price_growth_pct = (end_close - start_close) / start_close * 100
                if price_growth_pct > config.OI_MAX_PRICE_GROWTH_PCT:
                    continue

                avg_daily_vol_usd = (
                    sum(float(candle[4]) * float(candle[5]) for candle in aligned_candles) / len(aligned_candles)
                )
                if avg_daily_vol_usd < config.OI_MIN_AVG_DAILY_VOL_USD:
                    continue

                ts = int(aligned_oi[-1].get("ts", 0)) or int(datetime.now(tz=timezone.utc).timestamp() * 1000)
                signal = SignalEvent(
                    scanner_id=self.id,
                    symbol=MarketSymbol.from_raw(exchange, raw_symbol, market_type="linear_perp"),
                    timeframe="1d",
                    detected_at=datetime.now(timezone.utc),
                    candle_close_at=datetime.fromtimestamp(ts / 1000, timezone.utc),
                    score=min(1.0, growth_pct / 200),
                    metrics={
                        "oi_start": start,
                        "oi_end": end,
                        "oi_growth_pct": growth_pct,
                        "price_growth_pct": price_growth_pct,
                        "avg_daily_vol_usd": avg_daily_vol_usd,
                        "oi_usd": end * end_close,
                    },
                    ttl_seconds=config.OI_DAYS * 24 * 3600,
                )
                sort_value = self._sort_value(end, signal.metrics["avg_daily_vol_usd"], signal.metrics["price_growth_pct"], end_close)
                signals_with_sort.append((sort_value, signal))
        signals_with_sort.sort(key=lambda item: item[0], reverse=True)
        return [item[1] for item in signals_with_sort]
