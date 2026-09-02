# AGENTS.md

## Project Purpose

This repository analyzes whether major U.S. technology company news can predict the stock direction of the first regular trading session after the article is published.
The MVP compares a news-only baseline model against models that also include pre-article market sentiment and major policy/economic event flags.

## Core Research Question

Can pre-article market sentiment and major policy/economic event context improve prediction of whether the stock closes higher in the first regular session after the article?

## MVP Scope

Only work on the initial MVP unless explicitly asked to expand scope.
The MVP tickers are:

* NVDA
* AVGO
* AMD
* MU
* AAPL
* MSFT
* GOOGL
* TSLA

Do not add META, AMZN, WMT, COST, intraday price bars or other intraday price datasets, broker API integration, or real-time prediction unless the user explicitly asks for expansion after the MVP is working. Classifying an article by its intraday publication timestamp is still required.

## Market Benchmarks

Use `QQQ` as the Nasdaq-100 ETF benchmark and `SPY` as the S&P 500 ETF benchmark. They are market comparison series, not additions to the eight-company prediction universe and not initial model features.

Keep raw `close` values for audit. Use `adjusted_close` for price-direction labels and later benchmark-relative return calculations so stock splits and distributions do not create false price moves. Confirm the selected provider's adjustment method before using real data.

Normalize a price table once and reuse the prepared result across stock and benchmark lookups. A duplicate should exclude an article only when the requested `(ticker, trading_date)` key is ambiguous; unrelated duplicate keys belong in batch data-quality reporting and must not block another article.

Treat daily `trading_date` as an exchange-session date. Accept dates, ISO date strings, and timezone-naive midnight datetimes; reject timezone-aware datetimes instead of converting or truncating them.

Use one-session simple returns for the stock, QQQ, and SPY. Keep stock-minus-QQQ and stock-minus-SPY excess returns as separate evaluation fields. Do not use these future-return values as model features or replace the initial `up` / `not_up` target without explicit approval.

Calculate benchmark-relative returns only when the stock, QQQ, and SPY price pairs have identical previous and first-session trading dates. Reject mismatched periods instead of shifting benchmark dates automatically.

## Data Inputs

The MVP should use:

* article title
* article summary
* related ticker
* original article published timestamp
* market sentiment value available before the article
* major policy/economic event flag from the previous 24 hours

The initial event types are:

* TARIFF_POLICY
* FOMC
* CPI
* EMPLOYMENT

## Label Definition

The initial label is:

* `up`: the first regular-session adjusted close after the article is higher than the last confirmed adjusted close before the article
* `not_up`: both adjusted closes are valid and the first regular-session adjusted close is equal to or lower than the last confirmed adjusted close

Generate a label only when both adjusted-close prices are real, finite, and strictly positive. Reject missing values, strings, booleans, `NaN`, positive or negative infinity, and prices at or below zero with an explicit error that identifies the invalid field. Invalid prices must not silently become `not_up`.

Follow these initial rules:

* Pre-market article on a trading day: compare previous trading day adjusted close with same-day regular-session adjusted close
* Intraday article: compare previous trading day adjusted close with same-day regular-session adjusted close
* Ambiguous close-boundary article: from the actual session close through one minute after close, using the half-open interval `[actual_session_close_at_et, actual_session_close_at_et + 1 minute)`, do not select either label date; raise an explicit error and block label generation
* After-market article: from one minute after the actual session close, compare same-day regular-session adjusted close with next regular-session adjusted close
* Weekend/holiday article: compare previous open trading day adjusted close with next open trading day adjusted close

Use U.S. Eastern Time and the `exchange-calendars` `XNYS` schedule to decide whether an article is pre-market, intraday, after-market, weekend, or holiday. The one-minute close-confirmation window is a conservative MVP fallback until the selected price provider's actual close-availability timestamp is known.
On early-close days, use the actual regular-session close time from the `XNYS` schedule, not a fixed 16:00 cutoff. When calendar behavior is disputed or a hard-coded fixture date is added, verify the holiday or early-close schedule against an official NYSE notice.
Keep explicit calendar bounds that cover the MVP collection window. Expand them deliberately if the approved data period moves outside 2020-2030.
Do not classify sessions using naive local dates alone.

## Critical Rule: Prevent Data Leakage

Never use information that would not have been available at the article published time.
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

## Time Handling

Store original timestamps with source timezone when possible.
Normalize analysis timestamps to U.S. Eastern Time.
Use the `exchange-calendars` `XNYS` schedule for U.S. market holidays and early closes.
Avoid naive date-only joins.

Use explicit session boundary names in code, for example:

* `regular_session_open_at_et`
* `regular_session_close_at_et`
* `actual_session_close_at_et`
* `sentiment_available_at_et`
* `event_available_at_et`

When a source timestamp is ambiguous, keep the original value and record the normalization assumption.

## Duplicate Article Handling

Deduplicate articles conservatively during the MVP.
Prefer stable source identifiers in this order:

1. canonical URL
2. source article ID
3. normalized title + ticker + original published timestamp

Do not merge articles only because their titles are similar.
Treat article revisions as the same article only when the original published timestamp is preserved.
Do not use revision text or summary changes that were not available at `published_at_original`.

## Modeling Rules

Start simple.
Treat the following as dependency order for components that are not implemented yet, not as a statement of current progress. Before starting work, inspect the current code, tests, and relevant design notes instead of repeating or skipping work based only on this list.

Dependency order:

1. data schema
2. news collection feasibility sample
3. price data collection
4. timestamp normalization
5. label generation
6. baseline news-only model
7. sentiment-added model
8. event-flag-added model
9. time-based evaluation comparison

Use time-based train/validation/test splits.
Prefer interpretability over complex models during MVP.
Report Accuracy, Macro F1, and probability calibration/reliability when possible.

## Code Style

Prefer clear, small, testable functions.
Use explicit names for time-related variables, for example:

* `published_at_original`
* `published_at_et`
* `previous_confirmed_close_date`
* `first_regular_session_date`
* `event_window_start`
* `event_window_end`

Do not hide timezone or leakage logic inside vague helper names.

## Expected Project Structure

Prefer this structure when creating files:

* `src/global_news_market_impact/config/`: constants, ticker lists, event type definitions
* `src/global_news_market_impact/data/`: data collection and raw data loading
* `src/global_news_market_impact/features/`: timestamp joins, sentiment/event features
* `src/global_news_market_impact/labels/`: label generation
* `src/global_news_market_impact/models/`: baseline and comparison models
* `src/global_news_market_impact/evaluation/`: metrics and time-based validation
* `tests/`: unit tests for time logic, joins, and labels
* `notebooks/`: exploration only, not production logic
* `data/raw/`: raw data, ignored by git when large
* `data/processed/`: generated datasets, ignored by git when large
* `docs/`: design notes and experiment logs

Use CSV or Parquet for processed tabular datasets.
Keep raw source exports unchanged whenever possible.
Generated datasets, caches, credentials, notebooks checkpoints, and local experiment outputs must not be committed.

## Testing Priorities

Always prioritize tests for:

* market session selection
* weekend/holiday handling
* after-market article handling
* no future event leakage
* no future sentiment leakage
* ticker matching
* duplicate article handling

## Validation Workflow

Before editing, run `git status --short` and inspect the relevant implementation and tests. Preserve unrelated user changes in a dirty worktree.

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
* Do not suggest investment decisions based on model output.

## Do Not

* Do not expand the ticker universe before MVP completion.
* Do not introduce real-time trading or broker API features.
* Do not treat model output as financial advice.
* Do not optimize for high accuracy by leaking future information.
* Do not add heavy infrastructure before a working data pipeline exists.
