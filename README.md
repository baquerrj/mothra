# Simple Account Viewer

Local-only Python `Streamlit` app for checking-account spending analysis. The app ingests a CSV, normalizes transactions, detects likely recurring debits and credits, summarizes monthly cash flow, and surfaces budgeting insights.

## Run

```bash
python3 -m pip install -e ".[dev]"
streamlit run app.py
```

## Quality Gates

```bash
ruff check .
mypy spending_visualizer app.py
pytest
```
