"""Open interest scanner.

This scanner analyses changes in open interest for futures markets on
Binance. A significant increase in open interest relative to the
previous period may signal that new positions are being opened. To
reduce noise, the scanner also reports the corresponding price
change and average daily volume over the analysis window.

Due to the lack of network access in this environment, the default
implementation returns no signals. Replace the stubbed methods in
``adapters/binance.py`` or provide your own adapter implementation to
enable real data retrieval.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List

from .base import BaseScanner
from ..adapters.base import BaseExchangeAdapter
from ..models import SignalEvent, MarketSymbol
from .. import config


class OpenInterestScanner(BaseScanner):
    id = "oi_spike"
    name = "Open Interest Spike"

    async def scan(self, adapters: Dict[str, BaseExchangeAdapter]) -> List[SignalEvent]:
        signals: List[SignalEvent] = []
        for exch_id, adapter in adapters.items():
            # Only handle Binance for now
            if exch_id != "binance":
                continue
            symbols = await adapter.list_symbols()
            if not symbols:
                continue
            for sym in symbols:
                oi_hist = await adapter.fetch_open_interest_history(sym, days=config.OI_DAYS)
                if not oi_hist or len(oi_hist) < 2:
                    continue
                first_oi = oi_hist[0].get("oi")
                last_oi = oi_hist[-1].get("oi")
                if not first_oi or first_oi <= 0:
                    continue
                oi_change_pct = (last_oi - first_oi) / first_oi * 100.0
                if oi_change_pct < config.OI_GROWTH_PCT:
                    continue
                # Fetch daily candles for price/volume to compute metrics
                # We request one candle per day over OI_DAYS
                candles = await adapter.fetch_ohlcv(sym, timeframe="1d", limit=config.OI_DAYS)
                price_change_pct = 0.0
                avg_daily_vol = 0.0
                if candles and len(candles) >= 2:
                    try:
                        first_close = float(candles[0][4])
                        last_close = float(candles[-1][4])
                        price_change_pct = (last_close - first_close) / first_close * 100.0
                    except Exception:
                        pass
                    # Compute average daily USD volume
                    total = 0.0
                    for ts, o, h, l, c, v in candles:
                        try:
                            total += float(v) * float(c)
                        except Exception:
                            pass
                    avg_daily_vol = total / len(candles) if candles else 0.0
                # Compose signal
                last_timestamp_ms = oi_hist[-1].get("ts", 0)
                if last_timestamp_ms == 0:
                    # use current time as fallback
                    candle_close_at = datetime.now(timezone.utc)
                else:
                    candle_close_at = datetime.fromtimestamp(last_timestamp_ms / 1000, tz=timezone.utc)
                detected_at = datetime.now(timezone.utc)
                market_symbol = MarketSymbol.from_raw(exch_id, sym, market_type="linear_perp")
                metrics = {
                    "oi_change_pct": oi_change_pct,
                    "oi_first": first_oi,
                    "oi_last": last_oi,
                    "price_change_pct": price_change_pct,
                    "avg_daily_vol": avg_daily_vol,
                }
                # Use oi_change_pct normalised as score
                score = min(1.0, oi_change_pct / 200)  # 200% change maps to 1.0
                signals.append(
                    SignalEvent(
                        scanner_id=self.id,
                        symbol=market_symbol,
                        timeframe="1d",
                        detected_at=detected_at,
                        candle_close_at=candle_close_at,
                        direction=None,
                        score=score,
                        severity="INFO",
                        metrics=metrics,
                        ttl_seconds=config.OI_DAYS * 24 * 3600,
                    )
                )
        return signals