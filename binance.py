"""Data model definitions for the unified crypto signal bot.

The system uses dataclasses rather than plain dicts to represent
structured data. This provides type safety and makes it easier to
validate and document the expected shape of objects passed between
components. If you prefer Pydantic or another validation framework,
you may extend these classes accordingly.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass(frozen=True)
class MarketSymbol:
    """Representation of a market on a specific exchange.

    A ``MarketSymbol`` encapsulates the exchange identifier, the market
    type (e.g. spot or perpetual future) and the raw symbol string used
    by the exchange's API. Normalised attributes such as ``base_asset``
    and ``quote_asset`` are derived from the raw symbol but may be
    overridden explicitly when needed.
    """

    exchange: str
    market_type: str
    raw_symbol: str
    base_asset: str
    quote_asset: str
    is_active: bool = True

    def __post_init__(self) -> None:
        # Validate that base/quote assets are upper case for consistency
        object.__setattr__(self, "base_asset", self.base_asset.upper())
        object.__setattr__(self, "quote_asset", self.quote_asset.upper())

    @classmethod
    def from_raw(cls, exchange: str, raw_symbol: str, market_type: str = "spot") -> "MarketSymbol":
        """Factory method to derive base and quote assets from a raw symbol.

        This simple implementation splits on common delimiters. For more
        complex symbol formats (e.g. "BTC/USDT:USDT" used by some CCXT
        exchanges) you may need to override this logic in a subclass.
        """
        # Try splitting by '/', ':' or nothing
        base = raw_symbol
        quote = ""
        if "/" in raw_symbol:
            base, quote = raw_symbol.split("/", 1)
        elif ":" in raw_symbol:
            parts = raw_symbol.split(":", 1)[0].split("/")
            base = parts[0]
            quote = parts[1] if len(parts) > 1 else "USDT"
        else:
            # Assume last 4 characters are quote when they match USDT, USDC etc
            if raw_symbol.endswith("USDT"):
                base = raw_symbol[:-4]
                quote = "USDT"
            elif raw_symbol.endswith("USDC"):
                base = raw_symbol[:-4]
                quote = "USDC"
            else:
                quote = ""
        return cls(exchange=exchange.lower(), market_type=market_type, raw_symbol=raw_symbol,
                   base_asset=base, quote_asset=quote)


@dataclass
class SignalEvent:
    """Data class describing a trading signal produced by a scanner.

    Each signal has a unique identifier, a scanner id, associated
    ``MarketSymbol``, a timeframe (e.g. "1h"), detection timestamps,
    optional directional bias (long/short), a priority score, severity
    level and a deduplication key. Additional context may be provided
    via the ``metrics`` dictionary. The ``raw_data_hash`` field stores
    a hash of the underlying data used to compute the signal, enabling
    auditability and reproducibility of results.
    """

    scanner_id: str
    symbol: MarketSymbol
    timeframe: str
    detected_at: datetime
    candle_close_at: datetime
    direction: Optional[str] = None  # 'LONG' | 'SHORT' | None
    score: float = 0.0
    severity: str = "INFO"  # 'INFO' | 'WARNING' | 'CRITICAL'
    metrics: Dict[str, float] = field(default_factory=dict)
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    dedup_key: str = ""
    ttl_seconds: int = 3600
    raw_data_hash: str = ""
    model_version: Optional[str] = None

    def __post_init__(self) -> None:
        # Generate a deduplication key if not provided
        if not self.dedup_key:
            base = f"{self.scanner_id}:{self.symbol.exchange}:{self.symbol.raw_symbol}:{self.candle_close_at.isoformat()}"
            object.__setattr__(self, "dedup_key", hashlib.sha256(base.encode()).hexdigest())
        # Create a hash of the metrics for audit purposes
        if self.metrics and not self.raw_data_hash:
            # Serialise metrics to JSON deterministically
            metrics_json = json.dumps(self.metrics, sort_keys=True, separators=(",", ":"))
            object.__setattr__(self, "raw_data_hash", hashlib.sha256(metrics_json.encode()).hexdigest())


@dataclass
class UserSettings:
    """Per‑user settings controlling which signals are delivered.

    In a multi‑tenant deployment the bot may service many chat ids. Each
    chat can customise which scanners they receive signals from, which
    exchanges are considered, and other thresholds. In this simplified
    skeleton we include only a handful of fields; extend this class to
    capture additional preferences.
    """

    chat_id: int
    is_active: bool = True
    enabled_scanners: List[str] = field(default_factory=lambda: [
        "vol_spike", "price_pump", "oi_spike"
    ])
    enabled_exchanges: List[str] = field(default_factory=lambda: ["binance"])
    min_score_threshold: float = 0.0
    blacklist_symbols: List[str] = field(default_factory=list)
    timezone: str = "UTC"