# Simple Account Viewer

Local-only Python `Streamlit` app for checking-account spending analysis. The app ingests a CSV, normalizes transactions, detects likely recurring debits and credits, summarizes monthly cash flow, and surfaces budgeting insights.

## Run

```bash
python3 -m pip install -e ".[dev]"
streamlit run app.py
```

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
