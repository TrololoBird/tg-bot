"""Volume spike scanner.

Detects coins whose trading volume over the last 24 hours has grown by
at least ``MIN_VOL_RATIO`` relative to the previous 24 hours and whose
24‑hour volume exceeds ``MIN_VOL_USD_LAST``. The scanner operates on
hourly candles and processes each exchange independently before
deduplicating by base asset.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List

from .base import BaseScanner
from ..adapters.base import BaseExchangeAdapter
from ..models import SignalEvent, MarketSymbol
from .. import config


class VolumeSpikeScanner(BaseScanner):
    id = "vol_spike"
    name = "24h Volume Spike"

    async def scan(self, adapters: Dict[str, BaseExchangeAdapter]) -> List[SignalEvent]:
        signals: List[SignalEvent] = []
        # For each exchange, attempt to retrieve a list of symbols
        for exch_id, adapter in adapters.items():
            symbols = await adapter.list_symbols()
            if not symbols:
                continue

            # Filter candidate symbols by current tickers
            filtered_symbols: List[str] = []
            for sym in symbols:
                ticker = await adapter.fetch_ticker(sym)
                if not ticker:
                    continue
                last = ticker.get("last") or ticker.get("close")
                quote_vol = ticker.get("quoteVolume")
                if last is None:
                    continue
                # Derive USD volume from quoteVolume or baseVolume
                if quote_vol is None:
                    base_vol = ticker.get("baseVolume")
                    if base_vol is not None:
                        quote_vol = base_vol * last
                if quote_vol is None:
                    continue
                if quote_vol >= config.MIN_VOL_USD_LAST:
                    filtered_symbols.append(sym)

            for sym in filtered_symbols:
                # Fetch last 48 candles (hourly)
                candles = await adapter.fetch_ohlcv(sym, timeframe="1h", limit=48)
                if not candles or len(candles) < 24:
                    continue
                # Convert to lists of floats
                usd_vols: List[float] = []
                closes: List[float] = []
                for ts, o, h, l, c, v in candles:
                    try:
                        usd_vols.append(float(v) * float(c))
                        closes.append(float(c))
                    except Exception:
                        usd_vols.append(0.0)
                        closes.append(0.0)
                # Partition into last and previous 24
                if len(usd_vols) >= 48:
                    prev = usd_vols[:24]
                    last = usd_vols[24:48]
                else:
                    prev = usd_vols[:-24]
                    last = usd_vols[-24:]
                prev_vol = sum(prev)
                last_vol = sum(last)
                if prev_vol <= 0:
                    continue
                ratio = last_vol / prev_vol
                if last_vol >= config.MIN_VOL_USD_LAST and ratio >= config.MIN_VOL_RATIO:
                    # Determine candle close time (end of last candle)
                    last_timestamp_ms = candles[-1][0]
                    candle_close_at = datetime.fromtimestamp(last_timestamp_ms / 1000, tz=timezone.utc)
                    detected_at = datetime.now(timezone.utc)
                    base = sym.split("/")[0] if "/" in sym else sym[:-4] if sym.endswith("USDT") else sym
                    market_symbol = MarketSymbol.from_raw(exch_id, sym, market_type="linear_perp")
                    metrics = {
                        "prev_vol": prev_vol,
                        "last_vol": last_vol,
                        "ratio": ratio,
                    }
                    score = min(1.0, ratio / 10)  # simple normalisation
                    signals.append(
                        SignalEvent(
                            scanner_id=self.id,
                            symbol=market_symbol,
                            timeframe="1h",
                            detected_at=detected_at,
                            candle_close_at=candle_close_at,
                            direction=None,
                            score=score,
                            severity="INFO",
                            metrics=metrics,
                            ttl_seconds=24 * 3600,
                        )
                    )
        # Deduplicate by base coin: keep only highest ratio per base
        # We convert the list to a dict keyed by base_asset
        best_per_base: Dict[str, SignalEvent] = {}
        for s in signals:
            base = s.symbol.base_asset
            if base not in best_per_base or s.metrics.get("ratio", 0) > best_per_base[base].metrics.get("ratio", 0):
                best_per_base[base] = s
        return list(best_per_base.values())