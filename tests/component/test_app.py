from __future__ import annotations

from pathlib import Path

from _pytest.monkeypatch import MonkeyPatch
from streamlit.testing.v1 import AppTest


def write_named_csv(path: Path, contents: bytes) -> Path:
    path.write_bytes(contents)
    return path


def upload_checking_csv(
    app: AppTest,
    path: Path,
) -> AppTest:
    return app.file_uploader[0].set_value([(path.name, path.read_bytes(), "text/csv")]).run()


def upload_credit_card_csv(
    app: AppTest,
    path: Path,
) -> AppTest:
    return app.file_uploader[1].set_value([(path.name, path.read_bytes(), "text/csv")]).run()


def test_app_renders_dashboard_from_sample_csv(
    monkeypatch: MonkeyPatch,
    sample_csv_bytes: bytes,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("SPENDING_VISUALIZER_OVERRIDE_DIR", str(tmp_path))
    checking_file = write_named_csv(
        tmp_path / "wellsfargo__checking__1234.csv",
        sample_csv_bytes,
    )
    app = AppTest.from_file("app.py")
    app.run()
    upload_checking_csv(app, checking_file)
    assert len(app.exception) == 0
    assert any("Monthly Cash Flow" in heading.value for heading in app.subheader)
    assert any("Variable Recurring Expenses" in str(metric.label) for metric in app.metric)


def test_app_renders_credit_card_and_cross_account_views(
    monkeypatch: MonkeyPatch,
    sample_csv_bytes: bytes,
    sample_credit_card_csv_bytes: bytes,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("SPENDING_VISUALIZER_OVERRIDE_DIR", str(tmp_path))
    checking_file = write_named_csv(
        tmp_path / "wellsfargo__checking__1234.csv",
        sample_csv_bytes,
    )
    credit_card_file = write_named_csv(
        tmp_path / "wellsfargo__creditcard__9876.csv",
        sample_credit_card_csv_bytes,
    )
    app = AppTest.from_file("app.py")
    app.run()
    upload_checking_csv(app, checking_file)
    upload_credit_card_csv(app, credit_card_file)
    assert len(app.exception) == 0
    assert any("Approx. Current APR" in str(metric.label) for metric in app.metric)
    assert any("Cross-Account Payment Matches" in heading.value for heading in app.subheader)


def test_app_override_flow_updates_store(
    monkeypatch: MonkeyPatch,
    sample_csv_bytes: bytes,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("SPENDING_VISUALIZER_OVERRIDE_DIR", str(tmp_path))
    checking_file = write_named_csv(
        tmp_path / "wellsfargo__checking__1234.csv",
        sample_csv_bytes,
    )
    app = AppTest.from_file("app.py")
    app.run()
    upload_checking_csv(app, checking_file)
    if app.selectbox:
        app.selectbox[0].set_value("confirmed").run()
    assert (tmp_path / "overrides.json").exists()


def test_recurring_and_monthly_views_offer_csv_exports(
    monkeypatch: MonkeyPatch,
    sample_csv_bytes: bytes,
    sample_credit_card_csv_bytes: bytes,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("SPENDING_VISUALIZER_OVERRIDE_DIR", str(tmp_path))
    checking_file = write_named_csv(
        tmp_path / "wellsfargo__checking__1234.csv",
        sample_csv_bytes,
    )
    credit_card_file = write_named_csv(
        tmp_path / "wellsfargo__creditcard__9876.csv",
        sample_credit_card_csv_bytes,
    )
    app = AppTest.from_file("app.py")
    app.run()
    upload_checking_csv(app, checking_file)
    upload_credit_card_csv(app, credit_card_file)
    labels = [
        str(getattr(button, "label", ""))
        for button in app.get("download_button")
        if hasattr(button, "label")
    ]
    assert "Download monthly summary CSV" in labels
    assert "Download recurring expense breakdown CSV" in labels
    assert "Download variable recurring debits CSV" in labels
    assert "Download payment match candidates CSV" in labels


def test_invalid_filenames_are_rejected(
    monkeypatch: MonkeyPatch,
    sample_csv_bytes: bytes,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("SPENDING_VISUALIZER_OVERRIDE_DIR", str(tmp_path))
    invalid_file = write_named_csv(tmp_path / "wf_checking_1888.csv", sample_csv_bytes)
    app = AppTest.from_file("app.py")
    app.run()
    upload_checking_csv(app, invalid_file)
    assert any(
        "single underscores" in str(error.value)
        for error in app.error
    )


def test_invalid_upload_writes_diagnostic_log_file(
    monkeypatch: MonkeyPatch,
    sample_csv_bytes: bytes,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("SPENDING_VISUALIZER_OVERRIDE_DIR", str(tmp_path))
    log_path = tmp_path / "spending-visualizer.log"
    monkeypatch.setenv("SPENDING_VISUALIZER_LOG_FILE", str(log_path))
    invalid_file = write_named_csv(tmp_path / "wf_checking_1888.csv", sample_csv_bytes)
    app = AppTest.from_file("app.py")
    app.run()
    upload_checking_csv(app, invalid_file)
    assert log_path.exists()
    contents = log_path.read_text(encoding="utf-8")
    assert "Upload parsing failed" in contents
    assert "wf_checking_1888.csv" in contents
    assert "single underscores" in contents
    assert "expected_account_type=checking" in contents


def test_successful_upload_writes_account_metadata_to_log_file(
    monkeypatch: MonkeyPatch,
    sample_csv_bytes: bytes,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("SPENDING_VISUALIZER_OVERRIDE_DIR", str(tmp_path))
    log_path = tmp_path / "spending-visualizer.log"
    monkeypatch.setenv("SPENDING_VISUALIZER_LOG_FILE", str(log_path))
    checking_file = write_named_csv(
        tmp_path / "wellsfargo__checking__1234.csv",
        sample_csv_bytes,
    )
    app = AppTest.from_file("app.py")
    app.run()
    upload_checking_csv(app, checking_file)
    assert log_path.exists()
    contents = log_path.read_text(encoding="utf-8")
    assert "Upload parsed successfully" in contents
    assert "bank=wellsfargo" in contents
    assert "account_type=checking" in contents
    assert "account_number=1234" in contents


def test_transaction_descriptions_render_as_plain_text(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("SPENDING_VISUALIZER_OVERRIDE_DIR", str(tmp_path))
    sample = tmp_path / "bank__checking__1234.csv"
    sample.write_text(
        "Date,Amount,Description\n2026-01-01,-1.00,<script>alert(1)</script>\n",
        encoding="utf-8",
    )
    app = AppTest.from_file("app.py")
    app.run()
    upload_checking_csv(app, sample)
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
