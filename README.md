# Simple Account Viewer

Local-only Python `Streamlit` app for checking-account and credit-card analysis. The app ingests up to one checking CSV and one credit-card CSV, normalizes transactions, detects likely recurring debits and credits, summarizes monthly cash flow, estimates credit-card APR trends, and cross-references likely checking-to-card payments.

## Run

```bash
python3 -m pip install -e ".[dev]"
streamlit run app.py
```

Uploaded filenames must match `<bank>__<account_type>__<account_number>.csv`, where `account_type` is `checking` or `creditcard`.

Optional logging env vars:
- `SPENDING_VISUALIZER_LOG_FILE`: write application logs to a local file in addition to the terminal
- `SPENDING_VISUALIZER_LOG_LEVEL`: override the default log level (`INFO`)

## Requirements

The formal requirements and release updates are documented in [docs/requirements.md](/home/baquerrj/projects/simple-account-viewer/docs/requirements.md:1), and automated traceability lives in [docs/requirements_traceability.md](/home/baquerrj/projects/simple-account-viewer/docs/requirements_traceability.md:1).

## Quality Gates

```bash
nox -s lint
nox -s typecheck
nox -s tests
nox -s smoke
```

For a full local release gate, run `nox -s verify`.
