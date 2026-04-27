# Requirements Traceability

| Requirement | Automated Tests |
| --- | --- |
| `SYS-01` | `tests/unit/test_ingest.py::test_load_transactions_supports_headered_csv`, `tests/unit/test_ingest.py::test_load_transactions_supports_wells_fargo_style_csv` |
| `SYS-02` | `tests/unit/test_ingest.py::test_transaction_normalization_uses_decimal_and_source_rows` |
| `SYS-03` | `tests/unit/test_monthly.py::test_summarize_monthly_totals` |
| `SYS-04` | `tests/unit/test_recurring.py::test_detects_monthly_recurring_debits`, `tests/unit/test_recurring.py::test_detects_biweekly_recurring_credits`, `tests/unit/test_credit_card.py::test_credit_card_helpers_identify_payments_interest_and_fees` |
| `SYS-05` | `tests/unit/test_recurring.py::test_estimated_monthly_amount_scales_by_cadence`, `tests/component/test_services.py::test_build_report_computes_recurring_totals` |
| `SYS-06` | `tests/unit/test_insights.py::test_build_insights_emits_budgeting_signals` |
| `SYS-07` | `tests/component/test_services.py::test_override_store_persists_only_local_metadata`, `tests/component/test_app.py::test_app_renders_without_network_dependencies` |
| `SYS-08` | `tests/component/test_services.py::test_build_report_is_deterministic_for_same_input` |
| `SYS-09` | `tests/test_traceability.py::test_all_requirements_are_traced` |
| `SYS-10` | `tests/component/test_services.py::test_build_report_returns_expense_breakdown_and_variable_totals`, `tests/component/test_app.py::test_recurring_and_monthly_views_offer_csv_exports` |
| `SYS-11` | `tests/unit/test_recurring.py::test_detects_variable_monthly_recurring_debits`, `tests/unit/test_recurring.py::test_variable_recurring_estimate_uses_average_amount` |
| `SYS-12` | `tests/component/test_app.py::test_app_renders_credit_card_and_cross_account_views`, `tests/component/test_services.py::test_build_dashboard_bundle_matches_credit_card_payments` |
| `SYS-13` | `tests/unit/test_ingest.py::test_invalid_filename_raises_clear_errors`, `tests/component/test_app.py::test_invalid_filenames_are_rejected` |
| `SYS-14` | `tests/unit/test_payment_matching.py::test_match_credit_card_payments_scores_exact_amount_nearby_date_highly`, `tests/unit/test_payment_matching.py::test_confirmed_payment_match_receives_status_and_confidence_boost`, `tests/component/test_services.py::test_payment_match_decisions_are_keyed_by_account_pair` |
| `SYS-15` | `tests/unit/test_credit_card.py::test_estimate_interest_rate_returns_apr_and_trend`, `tests/component/test_app.py::test_app_renders_credit_card_and_cross_account_views` |
| `ING-01` | `tests/unit/test_ingest.py::test_load_transactions_supports_headered_csv`, `tests/unit/test_ingest.py::test_load_transactions_supports_wells_fargo_style_csv` |
| `ING-02` | `tests/unit/test_ingest.py::test_invalid_csv_raises_clear_errors` |
| `ING-03` | `tests/unit/test_ingest.py::test_transaction_normalization_uses_decimal_and_source_rows` |
| `ING-04` | `tests/unit/test_ingest.py::test_filename_parser_extracts_account_identity`, `tests/unit/test_ingest.py::test_load_transactions_supports_credit_card_csv` |
| `ANL-01` | `tests/unit/test_recurring.py::test_detects_monthly_recurring_debits` |
| `ANL-02` | `tests/unit/test_recurring.py::test_detects_biweekly_recurring_credits`, `tests/unit/test_recurring.py::test_detects_weekly_recurring_items` |
| `ANL-03` | `tests/unit/test_recurring.py::test_recurring_candidates_include_confidence_and_evidence_fields` |
| `ANL-04` | `tests/unit/test_monthly.py::test_summarize_monthly_totals`, `tests/unit/test_insights.py::test_build_insights_emits_budgeting_signals` |
| `ANL-05` | `tests/unit/test_recurring.py::test_variable_recurring_estimate_uses_average_amount`, `tests/component/test_services.py::test_build_report_returns_expense_breakdown_and_variable_totals` |
| `ANL-06` | `tests/unit/test_credit_card.py::test_credit_card_helpers_identify_payments_interest_and_fees`, `tests/component/test_services.py::test_build_dashboard_bundle_matches_credit_card_payments` |
| `ANL-07` | `tests/unit/test_payment_matching.py::test_match_credit_card_payments_enforces_one_to_one_pairing`, `tests/component/test_services.py::test_build_dashboard_bundle_matches_credit_card_payments` |
| `UI-01` | `tests/component/test_app.py::test_app_renders_dashboard_from_sample_csv` |
| `UI-02` | `tests/component/test_app.py::test_app_override_flow_updates_store` |
| `UI-03` | `tests/component/test_app.py::test_recurring_and_monthly_views_offer_csv_exports` |
| `UI-04` | `tests/component/test_app.py::test_recurring_and_monthly_views_offer_csv_exports` |
| `UI-05` | `tests/component/test_app.py::test_app_renders_credit_card_and_cross_account_views` |
| `PST-01` | `tests/component/test_services.py::test_override_store_persists_only_local_metadata` |
| `PST-02` | `tests/component/test_services.py::test_override_store_is_keyed_by_scope` |
| `PST-03` | `tests/component/test_services.py::test_payment_match_decisions_are_keyed_by_account_pair` |
| `QLT-01` | `.github/workflows/ci.yml`, `tests/smoke/test_smoke.py::test_streamlit_smoke_flow` |
| `QLT-02` | `noxfile.py`, `.github/workflows/ci.yml`, `README.md` |
| `ARC-01` | `tests/test_traceability.py::test_expected_package_layout_exists` |
| `ARC-02` | `tests/test_traceability.py::test_analysis_and_ingest_do_not_import_streamlit` |
| `ARC-03` | `tests/test_traceability.py::test_public_domain_types_exist` |
| `ARC-04` | `tests/test_traceability.py::test_domain_models_are_dataclasses` |
| `ARC-05` | `tests/test_traceability.py::test_expected_package_layout_exists`, `tests/test_traceability.py::test_packaging_uses_src_layout` |
| `ARC-06` | `tests/unit/test_ingest.py::test_filename_parser_extracts_account_identity`, `tests/component/test_services.py::test_payment_match_decisions_are_keyed_by_account_pair`, `tests/test_traceability.py::test_public_domain_types_exist` |
| `DSN-01` | `tests/unit/test_ingest.py::test_transaction_normalization_uses_decimal_and_source_rows` |
| `DSN-02` | `tests/unit/test_ingest.py::test_normalize_description_removes_card_noise` |
| `DSN-03` | `tests/unit/test_ingest.py::test_invalid_csv_raises_clear_errors` |
| `DSN-04` | `tests/component/test_app.py::test_transaction_descriptions_render_as_plain_text` |
| `DSN-05` | `tests/test_traceability.py::test_analysis_config_is_centralized` |
