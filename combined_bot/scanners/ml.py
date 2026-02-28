from __future__ import annotations

import hashlib
import pickle
from pathlib import Path
from typing import Dict, List, Optional

from ..adapters.base import BaseExchangeAdapter
from ..models import SignalEvent
from .base import BaseScanner


class MachineLearningScanner(BaseScanner):
    id = "ml_predictor"
    name = "ML Predictor"

    def __init__(self, model_path: Optional[Path] = None, expected_sha256: Optional[str] = None) -> None:
        self.model_path = model_path or Path("pump_predictor_model.pkl")
        self.expected_sha256 = expected_sha256
        self._model = None
        self._try_load_model()

    def _try_load_model(self) -> None:
        if not self.model_path.exists() or not self.expected_sha256:
            return
        file_hash = hashlib.sha256(self.model_path.read_bytes()).hexdigest()
        if file_hash != self.expected_sha256:
            return
        with self.model_path.open("rb") as model_file:
            self._model = pickle.load(model_file)

    async def scan(self, adapters: Dict[str, BaseExchangeAdapter]) -> List[SignalEvent]:
        _ = adapters
        return []
