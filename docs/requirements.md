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
