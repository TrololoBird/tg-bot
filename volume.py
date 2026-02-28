"""Scanner implementations for detecting interesting market events.

Each scanner inherits from ``BaseScanner`` and implements the
``scan`` coroutine. Scanners must be asynchronous because they may
perform network I/O or heavy computation. The ``scan`` method takes a
mapping of exchange adapters and returns a list of ``SignalEvent``
instances.

To add a new scanner, create a module in this package and register the
class in ``get_scanners`` within ``orchestrator.py``.
"""

from .base import BaseScanner
from .volume import VolumeSpikeScanner
from .price import PricePumpScanner
from .oi import OpenInterestScanner
from .ml import MachineLearningScanner

__all__ = [
    "BaseScanner",
    "VolumeSpikeScanner",
    "PricePumpScanner",
    "OpenInterestScanner",
    "MachineLearningScanner",
]