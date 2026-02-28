"""Machine learning based scanner.

This scanner loads a pretrained model (e.g. from a pickle file) and
applies it to derived features computed from recent OHLCV data. If the
model predicts a high probability of a positive price move, the
scanner generates a signal. The model file and feature engineering
logic are intentionally left as placeholders; in a real deployment
these should be replaced with a secure loading mechanism (e.g.
ONNX) and robust feature extraction.
"""

from __future__ import annotations

import asyncio
import pickle
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from .base import BaseScanner
from ..adapters.base import BaseExchangeAdapter
from ..models import SignalEvent, MarketSymbol
from .. import config


class MachineLearningScanner(BaseScanner):
    id = "ml_predictor"
    name = "ML Pump Predictor"

    def __init__(self, model_path: Optional[Path] = None) -> None:
        super().__init__()
        self.model_path = model_path or Path("pump_predictor_model.pkl")
        self._model = None
        # Attempt to load the model lazily
        try:
            if self.model_path.exists():
                with self.model_path.open("rb") as f:
                    # WARNING: pickle is unsafe! Only load models from
                    # trusted sources.
                    self._model = pickle.load(f)
        except Exception:
            self._model = None

    async def scan(self, adapters: Dict[str, BaseExchangeAdapter]) -> List[SignalEvent]:
        # If no model loaded, return empty list
        if self._model is None:
            return []
        signals: List[SignalEvent] = []
        # For demonstration we iterate over Binance symbols only
        adapter = adapters.get("binance")
        if not adapter:
            return []
        symbols = await adapter.list_symbols()
        for sym in symbols:
            # Fetch recent candles (e.g. last 50 1h candles)
            candles = await adapter.fetch_ohlcv(sym, timeframe="1h", limit=50)
            if not candles or len(candles) < 10:
                continue
            # Compute features (placeholder). A real implementation
            # would calculate RSI, moving averages, volume ratios, etc.
            # Here we simply compute percentage change in closing price
            closes = [float(c[4]) for c in candles if len(c) >= 5]
            if len(closes) < 10:
                continue
            pct_change = (closes[-1] - closes[0]) / closes[0]
            features = [pct_change]
            # Model expects a 2D array
            try:
                prob = float(self._model.predict_proba([features])[0][1])
            except Exception:
                continue
            threshold = 0.8
            if prob >= threshold:
                last_timestamp_ms = candles[-1][0]
                candle_close_at = datetime.fromtimestamp(last_timestamp_ms / 1000, tz=timezone.utc)
                detected_at = datetime.now(timezone.utc)
                market_symbol = MarketSymbol.from_raw("binance", sym, market_type="linear_perp")
                metrics = {
                    "ml_prob": prob,
                    "pct_change": pct_change,
                }
                score = prob
                signals.append(
                    SignalEvent(
                        scanner_id=self.id,
                        symbol=market_symbol,
                        timeframe="1h",
                        detected_at=detected_at,
                        candle_close_at=candle_close_at,
                        direction="LONG" if pct_change > 0 else "SHORT",
                        score=score,
                        severity="INFO",
                        metrics=metrics,
                        ttl_seconds=6 * 3600,
                        model_version="unknown",
                    )
                )
        return signals