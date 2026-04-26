# Requirements Traceability

| Requirement | Automated Tests |
| --- | --- |
| `SYS-01` | `tests/unit/test_ingest.py::test_load_transactions_supports_headered_csv`, `tests/unit/test_ingest.py::test_load_transactions_supports_wells_fargo_style_csv` |
| `SYS-02` | `tests/unit/test_ingest.py::test_transaction_normalization_uses_decimal_and_source_rows` |
| `SYS-03` | `tests/unit/test_monthly.py::test_summarize_monthly_totals` |
| `SYS-04` | `tests/unit/test_recurring.py::test_detects_monthly_recurring_debits`, `tests/unit/test_recurring.py::test_detects_biweekly_recurring_credits` |
| `SYS-05` | `tests/unit/test_recurring.py::test_estimated_monthly_amount_scales_by_cadence`, `tests/component/test_services.py::test_build_report_computes_recurring_totals` |
| `SYS-06` | `tests/unit/test_insights.py::test_build_insights_emits_budgeting_signals` |
| `SYS-07` | `tests/component/test_services.py::test_override_store_persists_only_local_metadata`, `tests/component/test_app.py::test_app_renders_without_network_dependencies` |
| `SYS-08` | `tests/component/test_services.py::test_build_report_is_deterministic_for_same_input` |
| `SYS-09` | `tests/test_traceability.py::test_all_requirements_are_traced` |
| `ING-01` | `tests/unit/test_ingest.py::test_load_transactions_supports_headered_csv`, `tests/unit/test_ingest.py::test_load_transactions_supports_wells_fargo_style_csv` |
| `ING-02` | `tests/unit/test_ingest.py::test_invalid_csv_raises_clear_errors` |
| `ING-03` | `tests/unit/test_ingest.py::test_transaction_normalization_uses_decimal_and_source_rows` |
| `ANL-01` | `tests/unit/test_recurring.py::test_detects_monthly_recurring_debits` |
| `ANL-02` | `tests/unit/test_recurring.py::test_detects_biweekly_recurring_credits`, `tests/unit/test_recurring.py::test_detects_weekly_recurring_items` |
| `ANL-03` | `tests/unit/test_recurring.py::test_recurring_candidates_include_confidence_and_evidence_fields` |
| `ANL-04` | `tests/unit/test_monthly.py::test_summarize_monthly_totals`, `tests/unit/test_insights.py::test_build_insights_emits_budgeting_signals` |
| `UI-01` | `tests/component/test_app.py::test_app_renders_dashboard_from_sample_csv` |
| `UI-02` | `tests/component/test_app.py::test_app_override_flow_updates_store` |
| `UI-03` | `tests/component/test_app.py::test_recurring_and_monthly_views_offer_csv_exports` |
| `PST-01` | `tests/component/test_services.py::test_override_store_persists_only_local_metadata` |
| `PST-02` | `tests/component/test_services.py::test_override_store_is_keyed_by_fingerprint` |
| `QLT-01` | `.github/workflows/ci.yml`, `tests/smoke/test_smoke.py::test_streamlit_smoke_flow` |
| `ARC-01` | `tests/test_traceability.py::test_expected_package_layout_exists` |
| `ARC-02` | `tests/test_traceability.py::test_analysis_and_ingest_do_not_import_streamlit` |
| `ARC-03` | `tests/test_traceability.py::test_public_domain_types_exist` |
| `ARC-04` | `tests/test_traceability.py::test_domain_models_are_dataclasses` |
| `DSN-01` | `tests/unit/test_ingest.py::test_transaction_normalization_uses_decimal_and_source_rows` |
| `DSN-02` | `tests/unit/test_ingest.py::test_normalize_description_removes_card_noise` |
| `DSN-03` | `tests/unit/test_ingest.py::test_invalid_csv_raises_clear_errors` |
| `DSN-04` | `tests/component/test_app.py::test_transaction_descriptions_render_as_plain_text` |
| `DSN-05` | `tests/test_traceability.py::test_analysis_config_is_centralized` |
