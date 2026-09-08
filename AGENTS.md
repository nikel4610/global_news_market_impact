# AGENTS.md

## Scope

Analyze historical U.S. technology-company news patterns and visualize subsequent return distributions and source evidence. Predictive-model training/comparison and sentiment/macro-event joins are deferred. New-article input and similar-case retrieval are follow-up work after validation.

Use only NVDA, AVGO, AMD, MU, AAPL, MSFT, GOOGL, and TSLA. QQQ and SPY are comparison benchmarks, not analysis tickers. Do not add other tickers, intraday price bars, or real-time prediction without explicit approval after the MVP works. Article publication-time classification remains required. Broker account/trading access remains prohibited, including as an expansion.

Never present historical up rates as validated future probabilities, associations as causal effects, or analysis as investment advice. Preserve existing contracts until an explicitly scoped implementation change. Do not finalize pattern categories, grouping rules, windows, thresholds, or interval estimators before sample review. Preserve the existing macro-event constants. Do not add heavy infrastructure before a working data pipeline exists.

## Task References

Reuse already-read instructions while current. Read only relevant sections, not every linked document.

| Task | Read before work |
| --- | --- |
| Select next step or check provider/implementation status | [design-notes.md](docs/design-notes.md): Current Status and Current Analysis Plan; verify relevant code before claiming completion |
| Change article/price preparation, labels, returns, or market sessions | [implementation-contracts.md](docs/implementation-contracts.md): Market Benchmarks, Label Data Contracts, Label Definition, Time Handling, as relevant |
| Change article deduplication | implementation-contracts.md: Duplicate Article Handling |
| Add files or choose checks | implementation-contracts.md: Code Style, Expected Project Structure, Testing Priorities, as relevant |
| Design ingestion, grouping, windows, or charts | design-notes.md: Current Guardrails and Current Analysis Plan; relevant README input/output sections |

Keep current status and next steps in design-notes.md, not here. Its Previous Implementation Plan is historical. Read Vault documents only for a requested planning/status task or Vault edit, following the Vault instructions.

## Data and Analysis Safeguards

Preserve original source exports and publication timezones; distinguish original, revised, and collected timestamps. Verify whether article text existed at publication and flag retrospective price commentary.

Preserve raw close for audit and use adjusted close for existing labels/returns. Require matching stock/QQQ/SPY window dates; reject invalid or ambiguous inputs explicitly rather than guessing or shifting dates. Before provider requests, enforce host/path allowlisting and credential redaction. Read design-notes.md, Current Status, for provider-date parsing and adjustment requirements before implementing ingestion. Keep raw provider data out of Git/public screens under its usage terms.

Discover explicit pattern rules in an earlier period and freeze them before later-period validation. Record candidates, exclusions, and counterexamples. Separate article deduplication from event grouping; preserve article IDs, report article/event counts separately, and flag overlapping stock/return windows. Show periods, window definitions, sample sizes, uncertainty, and stock/benchmark-relative results. Do not fabricate results or claim unimplemented charts exist.

## Brokerage API Safety Boundary

The Toss Securities integration is market-data-only. The sole approved origin is
`https://openapi.tossinvest.com`, with these method and path pairs:

* `POST /oauth2/token` for short-lived authentication
* `GET /api/v1/stocks`
* `GET /api/v1/candles`
* `GET /api/v1/market-calendar/US`

Reject any other method, path, or origin before sending a request. Never forward credentials across
a redirect or send `Authorization` to another origin. Never access, read, collect, or mutate:

* brokerage accounts or account identifiers
* cash, balances, buying power, or commissions
* holdings, positions, or sellable quantities
* orders, executions, order history, or conditional orders

Never send `X-Tossinvest-Account`, request or store `accountSeq`, or probe account, asset, order,
order-info, or conditional-order endpoints. Stop on requests for those capabilities.

Read credentials only from local environment variables and keep access tokens in memory. Never log,
display, persist, or commit credentials, tokens, account identifiers, or personal financial data;
redact credentials and tokens from errors and reports.

## Critical Rule: Prevent Data Leakage

Never use information unavailable at article publication to define article-time context or patterns. Future prices are measured outcomes only, and must stay separate from pattern inputs.
Do not use:

* article revisions after the original publish time
* market sentiment values finalized after the article
* policy/economic events published after the article
* same-day closing values as input features
* future price movement in feature engineering

When implementing joins, always compare exact timestamps, not only dates.
For sentiment and event data, prefer an explicit `available_at` timestamp when present.
If `available_at` is unavailable, use the most conservative timestamp that represents when the value could have been known, and document the assumption in the code or experiment log.
Do not join on `observed_at` or event date alone when the actual release or availability time may be later than the article timestamp.

## Validation Workflow

Before editing, run `git status --short` and inspect relevant target files; for code changes, also inspect the relevant implementation and tests. Preserve unrelated user changes in a dirty worktree.

After Python code changes, run:

1. `uv run --locked --extra dev pytest -q -p no:cacheprovider`
2. `uv run --locked --extra dev ruff check --no-cache .`
3. `uv run --locked --extra dev ruff format --no-cache --check <changed Python files>`
4. `git diff --check`

Do not format files outside the requested scope merely to make a repository-wide format check pass. Do not create a commit unless the user explicitly requests one.

## Response Rules

When explaining work:

* Start with the conclusion.
* Mention the files actually changed. For review-only work, state that no files were changed.
* Keep MVP scope small.
* Warn clearly when a proposed change may introduce data leakage.
* Do not suggest investment decisions based on analysis output.


For documentation-only changes, review changed text and local links and run `git diff --check`. Do not rerun Python checks unless executable behavior changes.
