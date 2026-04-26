from __future__ import annotations

from dataclasses import is_dataclass
from pathlib import Path

from spending_visualizer import config
from spending_visualizer.domain import models


def test_all_requirements_are_traced() -> None:
    traceability = Path("docs/requirements_traceability.md").read_text(encoding="utf-8")
    missing = [
        requirement_id
        for requirement_id in config.REQUIREMENT_IDS
        if requirement_id not in traceability
    ]
    assert not missing


def test_expected_package_layout_exists() -> None:
    for path in (
        Path("spending_visualizer/application"),
        Path("spending_visualizer/analysis"),
        Path("spending_visualizer/domain"),
        Path("spending_visualizer/ingest"),
        Path("spending_visualizer/persistence"),
        Path("spending_visualizer/ui"),
    ):
        assert path.exists()


def test_analysis_and_ingest_do_not_import_streamlit() -> None:
    for path in Path("spending_visualizer").rglob("*.py"):
        if "/ui/" in str(path):
            continue
        text = path.read_text(encoding="utf-8")
        if "/analysis/" in str(path) or "/ingest/" in str(path):
            assert "streamlit" not in text


def test_public_domain_types_exist() -> None:
    for attribute in ("Transaction", "RecurringCandidate", "MonthlySummary", "Insight"):
        assert hasattr(models, attribute)


def test_domain_models_are_dataclasses() -> None:
    for attribute in (
        models.Transaction,
        models.RecurringCandidate,
        models.MonthlySummary,
        models.Insight,
    ):
        assert is_dataclass(attribute)


def test_analysis_config_is_centralized() -> None:
    analysis_config = config.AnalysisConfig()
    assert analysis_config.minimum_occurrences == 3
