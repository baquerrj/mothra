from __future__ import annotations

from pathlib import Path

from _pytest.monkeypatch import MonkeyPatch
from streamlit.testing.v1 import AppTest


def test_streamlit_smoke_flow(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("SPENDING_VISUALIZER_OVERRIDE_DIR", str(tmp_path))
    app = AppTest.from_file("app.py")
    app.run()
    app.button[0].click().run()
    assert len(app.exception) == 0
    assert any("Recurring Debits" in markdown.value for markdown in app.markdown)
