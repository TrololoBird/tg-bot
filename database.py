"""Exchange adapter abstractions.

An adapter provides a unified interface for fetching market data from
different exchanges. Concrete implementations wrap specific APIs
or SDKs (e.g. CCXT) behind a consistent set of methods. All methods
must be coroutine compatible to allow asynchronous polling.

The adapters supplied in this package are intentionally minimal; they
return empty results by default because internet access is disabled in
this environment. To use them with real data, subclass
``BaseExchangeAdapter`` and override the relevant methods.
"""

from .base import BaseExchangeAdapter
from .binance import BinanceFuturesAdapter

__all__ = [
    "BaseExchangeAdapter",
    "BinanceFuturesAdapter",
]