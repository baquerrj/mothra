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
    assert Path("noxfile.py").exists()
    assert Path("docs/requirements.md").exists()
    for path in (
        Path("src/spending_visualizer/application"),
        Path("src/spending_visualizer/analysis"),
        Path("src/spending_visualizer/domain"),
        Path("src/spending_visualizer/ingest"),
        Path("src/spending_visualizer/persistence"),
        Path("src/spending_visualizer/ui"),
    ):
        assert path.exists()


def test_analysis_and_ingest_do_not_import_streamlit() -> None:
    for path in Path("src/spending_visualizer").rglob("*.py"):
        if "/ui/" in str(path):
            continue
        text = path.read_text(encoding="utf-8")
        if "/analysis/" in str(path) or "/ingest/" in str(path):
            assert "streamlit" not in text


def test_public_domain_types_exist() -> None:
    for attribute in (
        "Transaction",
        "RecurringCandidate",
        "RecurringExpenseBreakdownRow",
        "MonthlySummary",
        "Insight",
        "RecurringType",
    ):
        assert hasattr(models, attribute)


def test_domain_models_are_dataclasses() -> None:
    for attribute in (
        models.Transaction,
        models.RecurringCandidate,
        models.RecurringExpenseBreakdownRow,
        models.MonthlySummary,
        models.Insight,
    ):
        assert is_dataclass(attribute)


def test_analysis_config_is_centralized() -> None:
    analysis_config = config.AnalysisConfig()
    assert analysis_config.minimum_occurrences == 3
    assert analysis_config.variable_min_unique_amounts == 3


def test_packaging_uses_src_layout() -> None:
    pyproject_text = Path("pyproject.toml").read_text(encoding="utf-8")
    setup_text = Path("setup.py").read_text(encoding="utf-8")
    assert 'package-dir = {"" = "src"}' in pyproject_text
    assert 'package_dir={"": "src"}' in setup_text
