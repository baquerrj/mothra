from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from spending_visualizer.config import default_override_path
from spending_visualizer.domain.models import OverrideDecision


@dataclass
class OverrideStore:
    path: Path | None = None

    def __post_init__(self) -> None:
        if self.path is None:
            self.path = default_override_path()

    @property
    def _path(self) -> Path:
        assert self.path is not None
        return self.path

    def get_decisions(self, fingerprint: str) -> dict[str, OverrideDecision]:
        data = self._read()
        decisions = data.get(fingerprint, {})
        return {
            candidate_id: OverrideDecision(value)
            for candidate_id, value in decisions.items()
            if value in OverrideDecision._value2member_map_
        }

    def set_decision(
        self,
        fingerprint: str,
        candidate_id: str,
        decision: OverrideDecision,
    ) -> None:
        data = self._read()
        bucket = data.setdefault(fingerprint, {})
        bucket[candidate_id] = decision.value
        self._write(data)

    def _read(self) -> dict[str, dict[str, str]]:
        if not self._path.exists():
            return {}
        return cast(
            dict[str, dict[str, str]],
            json.loads(self._path.read_text(encoding="utf-8")),
        )

    def _write(self, data: dict[str, dict[str, str]]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
