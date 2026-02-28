from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from . import config


@dataclass(frozen=True)
class MarketSymbol:
    exchange: str
    market_type: str
    raw_symbol: str
    canonical_symbol: str
    base_asset: str
    quote_asset: str
    is_active: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "canonical_symbol", self.normalize_symbol(self.canonical_symbol))
        object.__setattr__(self, "base_asset", self.base_asset.upper())
        object.__setattr__(self, "quote_asset", self.quote_asset.upper())

    @staticmethod
    def normalize_symbol(raw_symbol: str) -> str:
        return raw_symbol.strip().upper().split(":", 1)[0]

    @classmethod
    def from_raw(cls, exchange: str, raw_symbol: str, market_type: str = "spot") -> "MarketSymbol":
        normalized = raw_symbol.strip().upper()
        tradable_symbol = cls.normalize_symbol(normalized)

        base = tradable_symbol
        quote = ""
        if "/" in tradable_symbol:
            base, quote = tradable_symbol.split("/", 1)
        else:
            for known_quote in config.KNOWN_QUOTE_ASSETS:
                if tradable_symbol.endswith(known_quote):
                    base, quote = tradable_symbol[: -len(known_quote)], known_quote
                    break
        return cls(
            exchange=exchange.lower(),
            market_type=market_type,
            raw_symbol=normalized,
            canonical_symbol=tradable_symbol,
            base_asset=base,
            quote_asset=quote,
        )


@dataclass
class SignalEvent:
    scanner_id: str
    symbol: MarketSymbol
    timeframe: str
    detected_at: datetime
    candle_close_at: datetime
    direction: Optional[str] = None
    score: float = 0.0
    severity: str = "INFO"
    metrics: Dict[str, float] = field(default_factory=dict)
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    dedup_key: str = ""
    ttl_seconds: int = 3600
    raw_data_hash: str = ""
    model_version: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.dedup_key:
            raw = f"{self.scanner_id}:{self.symbol.exchange}:{self.symbol.canonical_symbol}:{self.candle_close_at.isoformat()}"
            self.dedup_key = hashlib.sha256(raw.encode()).hexdigest()
        if self.metrics and not self.raw_data_hash:
            payload = json.dumps(self.metrics, sort_keys=True, separators=(",", ":"))
            self.raw_data_hash = hashlib.sha256(payload.encode()).hexdigest()


@dataclass
class UserSettings:
    chat_id: int
    is_active: bool = True
    enabled_scanners: List[str] = field(default_factory=lambda: ["vol_spike", "price_pump", "oi_spike"])
    enabled_exchanges: List[str] = field(default_factory=lambda: ["binance"])
    min_score_threshold: float = 0.0
    blacklist_symbols: List[str] = field(default_factory=list)
    timezone: str = "UTC"

    def __post_init__(self) -> None:
        self.enabled_scanners = [item.strip().lower() for item in self.enabled_scanners if item.strip()]
        self.enabled_exchanges = [item.strip().lower() for item in self.enabled_exchanges if item.strip()]
        self.blacklist_symbols = [
            MarketSymbol.normalize_symbol(item) for item in self.blacklist_symbols if item.strip()
        ]
