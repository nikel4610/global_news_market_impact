# AGENTS.md

## Project Purpose

Analyze keywords, phrases, event types, and context in historical U.S. technology-company news, then visualize subsequent stock-return distributions and source articles.
The direction changed on 2026-09-07 from predictive-model training to descriptive analysis and visualization. Model training and model-performance comparison are not current MVP tasks.
The MVP delivers a historical analysis explorer. New-article input and similar-case retrieval are follow-up work after data quality and later-period validation. Never present historical up rates as validated future probabilities or associations as causal effects.

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

Do not add META, AMZN, WMT, COST, intraday price bars, or real-time prediction unless the user
explicitly asks for expansion after the MVP is working. Broker account or trading integration is
not an expansion candidate and remains prohibited. Read-only public market-data access is allowed
only under the Brokerage API Safety Boundary. Classifying an article by its intraday publication
timestamp is still required.

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

## Data Inputs

The initial analysis requires article IDs, titles, summaries, source URLs, sources, related tickers, original publication timestamps with timezones, and stock/QQQ/SPY daily prices.
Distinguish original, revised, and collected timestamps and check whether text was available at original publication. Flag retrospective price-move commentary.
Pattern categories, phrase rules, grouping evidence, and event groups will be designed from actual samples; do not invent a finalized schema now.
Separate sentiment and macro-event ingestion/availability joins are deferred until needed after basic pattern analysis. Preserve the existing `TARIFF_POLICY`, `FOMC`, `CPI`, and `EMPLOYMENT` constants; they are not the finalized news-pattern taxonomy.

The 2026-09-04 sample-validation record selected Tiingo as primary for split- and cash-distribution-adjusted EOD prices; Toss is only a small public-data cross-check. No Tiingo adapter or full real dataset exists yet. Parse the provider date portion as `trading_date`, without timezone-shifting it. Enforce allowed hosts/paths and token redaction before implementing requests. Keep raw provider data out of Git and public displays under its usage terms.

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

## Analysis Windows

An intraday article's previous-close to same-day-close return includes pre-article movement; never call it a pure post-article response.
The initial direction is after-close to next-open news. Final inclusion of weekends/holidays, exact boundaries, return horizons, event-relative windows, minimum sample sizes, and interval estimators remain open until sample review.
Separate previous-close to next-close from next-open to close returns. Match adjustment bases when using opens; do not assume a reference price was executable at article time.

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

## Event Grouping

Article deduplication and grouping different articles about one event are separate operations. Preserve source articles and IDs. Do not count repeated coverage as independent events; report article and event counts separately and flag overlapping events in the same stock/return window. Final grouping rules require sample review.

## Analysis and Visualization Rules

Inspect current code, tests, README, and design notes before choosing the next incomplete step.
Start with manually checked, explicit keyword/phrase/event rules. Discover patterns in an earlier period, then freeze classification and aggregation rules for later-period validation.
Record candidates and exclusions, including counterexamples; avoid reporting only favorable patterns. Compare basic stock up rates and market-relative returns with sample sizes and uncertainty. Do not silently choose thresholds or intervals before the analysis-design step.
Plan four views: keyword/phrase trends, event-type return distributions, event-relative cumulative returns, and source-article/price case exploration. Display periods, article/event counts, exclusions, and window definitions; support stock versus QQQ/SPY-relative views. Do not fabricate measured results or claim unimplemented charts exist.
Next: news feasibility and samples -> classification/grouping/window design -> Tiingo ingestion and analysis dataset -> statistics and later-period validation -> visualization. Do not resume the old training plan.

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
* Do not suggest investment decisions based on analysis output.

## Do Not

* Do not expand the ticker universe before MVP completion.
* Do not introduce real-time trading or broker account and trading features.
* Do not treat analysis output as financial advice.
* Do not select favorable patterns by leaking future information.
* Do not add heavy infrastructure before a working data pipeline exists.
