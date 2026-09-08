# Implementation Contracts

Existing contracts moved from AGENTS.md verbatim. Read only the relevant sections before associated implementation changes. These are not a finalized event-study design. Project-wide safety remains in [AGENTS.md](../AGENTS.md); current status and analysis decisions remain in [design-notes.md](design-notes.md).

## Market Benchmarks

* Use `QQQ` and `SPY` as comparison benchmarks, not additional analysis tickers.
* Keep stock, QQQ, and SPY returns and both stock-minus-benchmark excess returns as separate analysis outcomes. Preserve existing feature-leakage guards.
* Continuous returns and distributions are primary analysis results; the existing binary label is an auxiliary historical summary, not a required modeling target.
* Require identical return-window dates across stock and benchmark price pairs. Reject mismatches instead of shifting benchmark dates.

## Label Data Contracts

* Preserve raw `close` for audit; use `adjusted_close` for labels and benchmark returns. Confirm the
  provider's adjustment method before real-data labeling.
* Normalize each price table once. Reject only a duplicate requested `(ticker, trading_date)` key;
  report unrelated duplicate keys as batch data-quality issues.
* Require `article_id`, `ticker`, and `published_at_et`, preserving row order and extra columns.
  Reject missing or duplicate normalized article IDs; keep bad tickers and times as row exclusions.
* Store `price_ticker`, `trading_date`, and optional `price_field` on structured price exclusions.
* Prepare article and price tables once per batch. Return stable, separate success and exclusion
  tables with zero-based `input_position`; join source text later by `article_id`.
* Treat `trading_date` as an exchange-session date. Accept dates, ISO strings, or timezone-naive
  midnight datetimes; reject timezone-aware datetimes instead of truncating them.

## Label Definition

These are existing code contracts, not a final definition of the new event-study window. Preserve them until a separately scoped implementation change. The existing label is:

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
* `src/global_news_market_impact/features/`: article pattern processing; sentiment/event joins deferred
* `src/global_news_market_impact/labels/`: label generation
* `src/global_news_market_impact/models/`: existing placeholder; training deferred
* `src/global_news_market_impact/evaluation/`: return statistics and later-period validation
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
* duplicate article handling and independent event grouping when implemented
* return-window alignment and pattern-input/outcome separation
* Toss allowlist enforcement, account-header rejection, and credential redaction
