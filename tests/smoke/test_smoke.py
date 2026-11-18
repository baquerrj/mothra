from __future__ import annotations

from pathlib import Path

from _pytest.monkeypatch import MonkeyPatch
from streamlit.testing.v1 import AppTest


def test_streamlit_smoke_flow(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
    sample_csv_bytes: bytes,
) -> None:
    monkeypatch.setenv("SPENDING_VISUALIZER_OVERRIDE_DIR", str(tmp_path))
    checking_file = tmp_path / "wellsfargo__checking__1234.csv"
    checking_file.write_bytes(sample_csv_bytes)
    app = AppTest.from_file("app.py")
    app.run()
    app.file_uploader[0].set_value(
        [(checking_file.name, checking_file.read_bytes(), "text/csv")]
    ).run()
    assert len(app.exception) == 0
    assert any("Recurring Debits" in markdown.value for markdown in app.markdown)
