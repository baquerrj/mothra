# Household budget design interview

Status: discovery in progress. These decisions describe the intended product, not features already implemented. The current user guide remains a guide to existing behavior.

## Agreed outcome

At each monthly review, the household can see whether its spending stayed within its plan, understand differences, and decide what to adjust next month.

## Agreed spending scope

Include hobby, non-essential, and miscellaneous purchases alongside essential spending. These purchases affect the money available for groceries and other needs; they must not be excluded simply because they are personal or discretionary.

## Agreed account coverage and budgeting behavior

- Include all checking accounts and credit cards used by household members, including individually owned accounts.
- Set monthly amounts by spending category and compare actual spending against them. Category amounts add up to the household spending plan; overspending remains visible until the user explicitly adjusts the plan.
- Count credit-card purchases against their categories when purchased. Treat subsequent repayments as settling debt, not another expense for those purchases.
- Track the cash needed for repayments, including earlier debt, separately from spending-plan performance.

## Agreed institution and account configuration

- An institution groups its credit-card, debit/checking, and savings accounts, as applicable. An institution need not have every account type.
- Savings balances appear in the household overview but are excluded from everyday spending availability until explicitly allocated or transferred. Transfers between household accounts are not income or expenses.
- Each account has a nickname in the MVP, with its owner or owners recorded separately. Joint accounts are entered once.
- A debit account means the underlying checking account: multiple debit cards linked to it share one account record and balance.
- An institution can hold multiple accounts of each supported type, including multiple credit-card accounts.
- Display the full account nickname and full account number, as explicitly requested. Do not substitute last-four-only display as the agreed behavior.
- All accounts use US dollars in the initial version.
- Closing an account preserves its transactions and historical reports while removing it from default choices for new transactions.

## Agreed direction for credit-card configuration

Prefer credit-card configuration and balances, including credit limits and amounts owed, obtained from processed statements. Direct institution/API connections are a possible future update, not a committed initial integration. Manual entry and correction are available for missing or incorrectly extracted information and unsupported statement formats.

Statement processing covers credit-card, checking, and savings accounts for explicitly supported formats. Before saving, show extracted institution, account number, statement date, balance, and applicable credit limit, minimum payment, and due date for review. Missing fields remain visibly unknown until supplied.

Keep the statement balance separately from the current recorded balance updated by later transactions. Importing an older statement must not reset the current balance or count transactions again. Track each card statement's minimum payment and due date, and payments toward that statement's obligation; keep minimum due, statement balance, and current balance distinct.

## Agreed statement matching and reconciliation

- Suggest matches between imported transactions and transactions already entered manually; let the user resolve uncertain matches. The same purchase must not count twice.
- Show differences between recorded activity and statement balances. Allow correction of missing or incorrect transactions before accepting an explicit balance adjustment; never silently replace the balance or invent an expense to hide a difference.
- Suggest which card statement a payment satisfies, allow corrections, and mark uncertain assignments for review. Display remaining minimum payment and remaining statement balance separately. Detailed assignment rules remain to be designed.
- When a statement provides only the last four account-number digits, automatically select an account only when exactly one existing account matches those digits and the institution and account type, when identifiable. With multiple matches or no match, prompt the user to select the correct account. The selection remains visible and changeable during import review.
- If no existing account is correct, offer account creation within the import flow, prefilled with extracted information. Ask for missing details including nickname, full account number, and ownership without restarting the import.
- Explicit balance adjustments require a date and reason, remain visible in account history, and are excluded from spending and income totals. A known missing purchase or fee should instead be entered as a transaction so that it affects the budget.

## Agreed payment-source tracking

Track the actual payment account for each transaction, including whether it used checking/debit or a named credit card. Categories do not need planned allocations between payment sources. The user wants card use visible because purchases consume the category budget and create repayment obligations. Available credit is neither household income nor cash and does not increase a category budget.

For example, a $100 grocery purchase on a credit card consumes $100 of the grocery budget and creates a $100 card repayment obligation. Paying that card later reduces cash and settles debt without counting the purchase again.

## Agreed monthly rollover behavior

Category budgets reset each month by default. Allow explicit rollover of unused amounts for selected categories, such as an occasional grooming expense. Rollover increases the category's spending allowance; it does not establish that cash has been set aside. Treatment of overspending across month boundaries remains to be defined.

## Agreed manual-entry workflow

Start with manually entered balances and transactions for all household checking/debit and credit-card accounts. Manual transaction entry is part of the intended workflow, rather than requiring CSV imports after entering an opening balance. A debit card uses its linked checking account; its balance is not a separate pool of money.

Each account starts with a balance as of a chosen date, entered manually or accepted from a reviewed statement; subsequent transactions update that balance automatically. For checking and savings accounts the balance represents money held; for credit cards it represents money owed.

This extends the current CSV-analysis app with an intended account and transaction record-keeping workflow; it is not already implemented. Detailed transaction correction and reconciliation rules remain to be defined. The role of existing CSV imports alongside manual entry also remains open.

## Remaining statement-import proposals (not yet agreed)

Consider local PDF statement import as an optional aid for historical entry, with extraction preview, corrections, duplicate review, and statement-balance reconciliation before acceptance. Prefer CSV when available; initially support known digital statement layouts, with scanned/OCR statements deferred. PDF text extraction alone does not reliably recover table structure, and image-only statements require OCR ([pypdf extraction documentation](https://github.com/py-pdf/pypdf/blob/main/docs/user/extract-text.md)).

Proposed history target: start with three complete months across all relevant accounts, and aim for twelve months to include seasonal and annual expenses. This is a planning recommendation, not a guarantee of statistical stability. The [Florida Department of Financial Services](https://www.myfloridacfo.com/ymm/SavingAndSpending/Budgeting) suggests three-month averages for varying expenses; the [CFPB](https://www.consumerfinance.gov/owning-a-home/prepare/assess-your-spending/) advises reviewing several months for less frequent expenses. The twelve-month target is our inference to cover a full annual cycle.

Historical imports before an account's opening-balance date must not be applied again to that balance. Define whether they are analysis-only history or whether the account is rebased to an earlier reconciled opening balance before implementation.

## Open decisions

- Detailed transaction correction and explicit balance-adjustment behavior.
- Detailed payment assignment rules and calculation of remaining available credit.
- Whether CSV imports remain an optional input alongside manual transactions; detailed duplicate detection rules.
- Treatment of overspending across month boundaries, including categories with rollover enabled.
- Income, savings, irregular expenses, and review/correction workflows, to be explored after their prerequisites are settled.

## Evidence and terminology

The [project research](/home/baquerrj/projects/simple-account-viewer/docs/research/project-overview.md) describes current behavior and limitations. The [glossary](/home/baquerrj/projects/simple-account-viewer/GLOSSARY.md) records agreed terms. No implementation plan or architecture decision is finalized yet.
