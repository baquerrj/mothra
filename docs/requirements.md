# Requirements

## v1.0.0 Baseline
- The application shall ingest local checking-account CSV files and normalize transactions into typed records.
- The application shall summarize monthly cash flow and detect recurring debits and recurring credits.
- The application shall keep banking data on the local machine and provide automated verification for core behavior.

## v1.0.1 Updates
- `SYS-10`: The application shall provide a merchant-level estimated monthly recurring-expense breakdown for recurring debits.
- `SYS-11`: The application shall distinguish fixed recurring debits from variable recurring debits when cadence is consistent but payment values change.
- `ANL-05`: The recurring analysis subsystem shall compute average, min, and max values for recurring debit merchants and use the average amount when estimating variable recurring monthly expenses.
- `UI-04`: The UI shall expose a dedicated variable recurring debit view and a recurring-expense breakdown view with CSV exports.
- `QLT-02`: The repository shall use `nox` as the canonical task runner for lint, type checks, tests, smoke checks, and CI verification.
- `ARC-05`: Application source code shall be organized under `src/` while keeping a thin top-level app launcher for local Streamlit execution.

## v1.1.0 Updates
- `SYS-12`: The application shall accept up to one checking CSV and one credit-card CSV in the same local dashboard session.
- `SYS-13`: The application shall require uploaded CSV filenames to match `<bank>__<account_type>__<account_number>.csv` and reject uploads that do not satisfy that contract.
- `SYS-14`: The application shall cross-reference likely checking-account debits and credit-card payment credits, assign confidence, and allow local confirm or reject feedback on those matches.
- `SYS-15`: The application shall estimate a current approximate credit-card APR and recent interest trend with explicit caveats.
- `ING-04`: The ingestion subsystem shall parse filename-derived bank name, account type, and account number metadata and attach it to normalized transactions.
- `ANL-06`: The analysis subsystem shall identify explicit credit-card payment credits, interest charges, and late fees from credit-card transaction histories.
- `ANL-07`: The analysis subsystem shall perform one-to-one matching between checking debits and credit-card payment credits using amount, date, and descriptor heuristics.
- `UI-05`: The UI shall provide separate checking, credit-card, and cross-account views when the corresponding account data is available.
- `PST-03`: The persistence subsystem shall store payment-match feedback separately from recurring-candidate feedback and scope both to account-aware identifiers.
- `ARC-06`: The architecture shall treat account identity as a first-class concern across ingestion, reporting, analysis, and override persistence.
