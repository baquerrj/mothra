from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from spending_visualizer.config import default_override_path
from spending_visualizer.domain.models import OverrideDecision

RECURRING_NAMESPACE = "recurring"
PAYMENT_MATCH_NAMESPACE = "payment_matches"
OverridePayload = dict[str, dict[str, dict[str, str]]]


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

    def get_decisions(self, scope_key: str) -> dict[str, OverrideDecision]:
        return self._get_namespace_decisions(RECURRING_NAMESPACE, scope_key)

    def set_decision(
        self,
        scope_key: str,
        candidate_id: str,
        decision: OverrideDecision,
    ) -> None:
        self._set_namespace_decision(RECURRING_NAMESPACE, scope_key, candidate_id, decision)

    def get_payment_match_decisions(self, scope_key: str) -> dict[str, OverrideDecision]:
        return self._get_namespace_decisions(PAYMENT_MATCH_NAMESPACE, scope_key)

    def set_payment_match_decision(
        self,
        scope_key: str,
        match_id: str,
        decision: OverrideDecision,
    ) -> None:
        self._set_namespace_decision(PAYMENT_MATCH_NAMESPACE, scope_key, match_id, decision)

    def _get_namespace_decisions(
        self,
        namespace: str,
        scope_key: str,
    ) -> dict[str, OverrideDecision]:
        data = self._read()
        decisions = data.get(namespace, {}).get(scope_key, {})
        return {
            candidate_id: OverrideDecision(value)
            for candidate_id, value in decisions.items()
            if value in OverrideDecision._value2member_map_
        }

    def _set_namespace_decision(
        self,
        namespace: str,
        scope_key: str,
        item_key: str,
        decision: OverrideDecision,
    ) -> None:
        data = self._read()
        namespace_bucket = data.setdefault(namespace, {})
        scope_bucket = namespace_bucket.setdefault(scope_key, {})
        scope_bucket[item_key] = decision.value
        self._write(data)

    def _read(self) -> OverridePayload:
        if not self._path.exists():
            return {}
        raw = cast(dict[str, object], json.loads(self._path.read_text(encoding="utf-8")))
        if RECURRING_NAMESPACE in raw or PAYMENT_MATCH_NAMESPACE in raw:
            return cast(OverridePayload, raw)
        return {RECURRING_NAMESPACE: cast(dict[str, dict[str, str]], raw)}

    def _write(self, data: Mapping[str, object]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
