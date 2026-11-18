# Household budget tracking with Simple Account Viewer

Use Simple Account Viewer to review your household's recorded income, spending, and recurring bills from bank exports. This guide describes the current app. It helps you gather information for a budget; it does not yet let you enter category budgets, compare spending against targets, or calculate a household-wide amount available to spend.

You can review **one checking account and one credit card at a time**. If your household uses additional accounts, the dashboard will show only part of its finances.

## 1. Start the app

From a terminal in the `simple-account-viewer` project directory, create a Python environment and install the app once:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

Start the dashboard:

```bash
python -m streamlit run app.py
```

Open the local address printed in the terminal. On later visits, activate the same environment and run the start command again. Stop the app with `Ctrl+C` in that terminal.

## 2. Prepare your bank exports

Download a checking-account CSV and, optionally, a credit-card CSV from your bank. Start with at least three complete months so the app has a chance to identify recurring payments. Use the same date range for both accounts when reviewing card payments.

The supported headered format contains `Date`, `Amount`, and `Description` columns; capitalization does not matter. A `Status` column is optional. Dates can be `2026-01-31` or `01/31/2026`. Outflows must be negative and inflows positive. The app also supports some headerless bank exports, but it does not offer a column-mapping screen for other formats.

Rename your files using this pattern:

```text
<bank>__<account_type>__<account_number>.csv
```

For example:

```text
examplebank__checking__1234.csv
examplebank__creditcard__5678.csv
```

Use two underscores between each part. Account type must be `checking` or `creditcard`. Bank and account labels may contain letters, numbers, and hyphens. Use a consistent short account label, such as the last four digits, instead of a full account number: the app displays and logs this label.

## 3. Upload and check the results

Upload each file into its matching checking or credit-card upload box. You can begin with just one file. With both loaded, the dashboard provides **Checking**, **Credit Card**, and **Cross-Account** views.

Check the **Transactions** view first. Compare a few dates, descriptions, and amounts with your export. If a file is rejected, check its name, columns, dates, and amount format. Use your own exports for this workflow; the sample buttons depend on local files that may not be available.

## 4. Review monthly cash flow

Use **Monthly Cash Flow** to review:

- **Total In:** all positive transactions in the account, including transfers or refunds.
- **Total Out:** all negative transactions, shown as a positive total.
- **Net:** Total In minus Total Out for the month.

These are transaction totals, not your current account balance. An incomplete month can look unusually low. The app includes supplied rows without removing duplicates or filtering pending transactions, so choose your export carefully.

For a household review, record which complete months had more money going out than coming in. Use **Insights** to identify months or merchants worth examining, then check the underlying transactions before drawing conclusions.

## 5. Review recurring bills and income

Open **Recurring Debits** for likely repeating outflows and **Variable Recurring Debits** for repeating outflows whose amounts change. **Expense Breakdown** shows estimated monthly amounts by merchant. **Recurring Credits** shows likely repeating inflows.

These are suggestions based on transaction patterns. The app looks for weekly, biweekly, and monthly repetition; it can miss annual bills or expenses with changing descriptions. A monthly estimate is an average or typical amount adjusted for frequency, not a bill forecast or a spending limit.

Use each candidate's selector to leave it automatic, confirm it, or reject it. Feedback saves locally immediately; displayed results update after a short delay. Rejected items disappear from the results, and there is currently no separate screen for restoring them. Recurring confirmation records your choice but does not change the estimate.

## 6. Review credit-card payments separately

The **Credit Card** view shows recognized payments, interest charges, late fees, and an approximate APR when enough usable history exists. Recognition depends on particular transaction descriptions, so missing details do not establish that no interest or fees were charged. Check your statement for the actual APR.

With both files loaded, open **Cross-Account** to review likely checking-to-card payments. Compare the two dates, amounts, descriptions, and confidence before confirming or rejecting a match. Automatic matches are already included in the displayed matched-payment total.

**Do not add checking Total Out and credit-card Total Out to estimate household spending.** A card purchase and the checking payment that settles it can both appear in those totals. Matching helps you inspect transfers, but the app does not subtract them from a combined household report.

## 7. Save your review and repeat

Use the download buttons to save monthly summaries, recurring-expense breakdowns, transactions, or payment matches. A practical monthly review is to check a complete month's cash flow, review recurring bills, inspect card payments, and export the results. Keep budget targets and decisions in your own worksheet until target tracking is added to the app.

Upload fresh exports for your next review. The app does not maintain a growing transaction history or merge new exports with old ones. Feedback belongs to the exact uploaded file contents; adding rows or changing the file can mean earlier decisions are not applied.

## Where your information goes

Run the app on your own computer for the intended local workflow. It does not connect to your bank. Treat the dashboard, exported reports, and logs as private financial information.

Feedback is saved by default in `~/.simple_account_viewer/overrides.json`. This is a plaintext file whose identifiers can include account labels and merchant names. Upload logs include filenames and account labels; optional file logging creates another local copy of that metadata. “Local” does not mean encrypted or protected from other people who can access your computer.

## About this guide

This guide was checked against the current working-tree implementation, including uncommitted changes, rather than a tested release. Setup and UI steps have not been executed as part of this documentation task. The [research report](/home/baquerrj/projects/simple-account-viewer/docs/research/project-overview.md) provides source citations and a fuller account of known limitations. The [requirements](/home/baquerrj/projects/simple-account-viewer/docs/requirements.md) describe the documented product behavior.
