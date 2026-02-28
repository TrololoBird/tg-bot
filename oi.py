"""Price pump scanner.

Detects coins whose price has risen significantly over the last 24
hours relative to its price 24 hours ago. In addition, a minimum
24‑hour traded volume in USD must be met. This scanner uses the
same adapter interface as other scanners.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Dict, List

from .base import BaseScanner
from ..adapters.base import BaseExchangeAdapter
from ..models import SignalEvent, MarketSymbol
from .. import config


class PricePumpScanner(BaseScanner):
    id = "price_pump"
    name = "24h Price Pump"

    async def scan(self, adapters: Dict[str, BaseExchangeAdapter]) -> List[SignalEvent]:
        signals: List[SignalEvent] = []
        for exch_id, adapter in adapters.items():
            symbols = await adapter.list_symbols()
            if not symbols:
                continue
            for sym in symbols:
                # Fetch last 24 candles (hourly)
                candles = await adapter.fetch_ohlcv(sym, timeframe="1h", limit=24)
                if not candles or len(candles) < 2:
                    continue
                # Compute first and last close
                try:
                    first_close = float(candles[0][4])
                    last_close = float(candles[-1][4])
                except Exception:
                    continue
                if first_close <= 0:
                    continue
                price_ratio = last_close / first_close
                # Compute 24h volume in USD
                usd_vol = 0.0
                for ts, o, h, l, c, v in candles:
                    try:
                        usd_vol += float(v) * float(c)
                    except Exception:
                        pass
                if price_ratio >= config.MIN_PRICE_RATIO and usd_vol >= config.MIN_VOL_USD_LAST:
                    last_timestamp_ms = candles[-1][0]
                    candle_close_at = datetime.fromtimestamp(last_timestamp_ms / 1000, tz=timezone.utc)
                    detected_at = datetime.now(timezone.utc)
                    market_symbol = MarketSymbol.from_raw(exch_id, sym, market_type="linear_perp")
                    metrics = {
                        "price_ratio": price_ratio,
                        "vol_24h": usd_vol,
                    }
                    # Score normalised between 0 and 1; 1.3 ratio yields 0.3, etc
                    score = min(1.0, price_ratio - 1.0)
                    signals.append(
                        SignalEvent(
                            scanner_id=self.id,
                            symbol=market_symbol,
                            timeframe="1h",
                            detected_at=detected_at,
                            candle_close_at=candle_close_at,
                            direction="LONG",
                            score=score,
                            severity="INFO",
                            metrics=metrics,
                            ttl_seconds=24 * 3600,
                        )
                    )
        # Deduplicate by base asset: keep highest price_ratio
        best_per_base: Dict[str, SignalEvent] = {}
        for s in signals:
            base = s.symbol.base_asset
            if base not in best_per_base or s.metrics.get("price_ratio", 0) > best_per_base[base].metrics.get("price_ratio", 0):
                best_per_base[base] = s
        return list(best_per_base.values())