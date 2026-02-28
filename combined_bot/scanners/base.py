from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List

from ..adapters.base import BaseExchangeAdapter
from ..models import SignalEvent


class BaseScanner(ABC):
    id = "base"
    name = "Base Scanner"

    @abstractmethod
    async def scan(self, adapters: Dict[str, BaseExchangeAdapter]) -> List[SignalEvent]:
        raise NotImplementedError
