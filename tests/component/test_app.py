from __future__ import annotations

from pathlib import Path

from _pytest.monkeypatch import MonkeyPatch
from streamlit.testing.v1 import AppTest


def test_app_renders_dashboard_from_sample_csv(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("SPENDING_VISUALIZER_OVERRIDE_DIR", str(tmp_path))
    app = AppTest.from_file("app.py")
    app.run()
    app.button[0].click().run()
    assert len(app.exception) == 0
    assert any("Monthly Cash Flow" in heading.value for heading in app.subheader)


def test_app_override_flow_updates_store(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("SPENDING_VISUALIZER_OVERRIDE_DIR", str(tmp_path))
    app = AppTest.from_file("app.py")
    app.run()
    app.button[0].click().run()
    if app.selectbox:
        app.selectbox[0].set_value("confirmed").run()
    assert (tmp_path / "overrides.json").exists()


def test_recurring_and_monthly_views_offer_csv_exports(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("SPENDING_VISUALIZER_OVERRIDE_DIR", str(tmp_path))
    app = AppTest.from_file("app.py")
    app.run()
    app.button[0].click().run()
    assert len(app.get("download_button")) >= 3


def test_transaction_descriptions_render_as_plain_text(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("SPENDING_VISUALIZER_OVERRIDE_DIR", str(tmp_path))
    sample = tmp_path / "malicious.csv"
    sample.write_text(
        "Date,Amount,Description\n2026-01-01,-1.00,<script>alert(1)</script>\n",
        encoding="utf-8",
    )
    app = AppTest.from_file("app.py")
    app.run()
    app.file_uploader[0].set_value(
        [(sample.name, sample.read_bytes(), "text/csv")]
    ).run()
    assert len(app.exception) == 0
    table_text = "".join(str(table.value) for table in app.dataframe)
    assert "SCRIPT ALERT SCRIPT" in table_text


def test_app_renders_without_network_dependencies(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("SPENDING_VISUALIZER_OVERRIDE_DIR", str(tmp_path))
    app = AppTest.from_file("app.py")
    app.run()
    assert any("Data stays on this machine" in str(info.value) for info in app.info)
