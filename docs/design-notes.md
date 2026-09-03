# Design Notes

## MVP Focus

The MVP tests whether adding pre-article market sentiment and major policy or economic event flags improves prediction over a news-only baseline.

The first implementation should avoid model complexity and focus on:

1. Data schema.
2. Timestamp normalization.
3. Market-session selection.
4. Label generation.
5. Leakage-safe feature joins.

## Current Guardrails

- Use only the MVP tickers defined in `src/global_news_market_impact/config/tickers.py`.
- Use only the MVP event types defined in `src/global_news_market_impact/config/events.py`.
- Keep QQQ and SPY as Nasdaq-100 and S&P 500 comparison benchmarks, not model features.
- Normalize analysis timestamps to U.S. Eastern Time.
- Use an exchange calendar for U.S. market holidays and early closes.
- Compare exact timestamps, not only dates.
- Do not use data that was unavailable at `published_at_original`.

## Current Status

Completed:

- Source and training-row column contracts, including paired `*_original` and `*_et` timestamps.
- Minimum article-label input preparation with required columns, non-empty unique IDs, stable input order, and retained extra columns.
- Market-session selection for pre-market, intraday, after-market, weekend, holiday, and early-close cases.
- A conservative one-minute ambiguous close-boundary rejection rule.
- Basic validation that both label prices are real, finite, and strictly positive.
- Schema contract tests that separate audit, feature, label-generation, and target columns.
- Fixture-based price-row validation and selection for the article ticker, QQQ, and SPY.
- Reusable prepared price tables and key-local duplicate checks so unrelated duplicate rows do not exclude another article.
- Strict session-date inputs that reject timezone-aware daily-price datetimes instead of truncating them.
- End-to-end adjusted-close label generation with structured exclusion reasons and explicit affected ticker, trading date, and price field.
- Batch label generation with one-time article/price preparation, stable success/exclusion schemas, and zero-based input positions.
- One-session simple returns for the stock, QQQ, and SPY, plus separate excess returns versus each benchmark.
- Trading-date alignment checks across the stock, QQQ, and SPY before return calculation.
- Schema guards that keep all return and excess-return evaluation fields out of model features.

Not implemented:

- Real-provider price ingestion, batch label output, and exclusion-reason aggregation.
- Runtime timestamp normalization and availability-safe joins.
- News, price, sentiment, and event provider feasibility validation or collection.
- Model training, time-based evaluation, and experiment reporting.

## Initial Implementation Plan

### Step 1: Schema and constants

Create the stable MVP constants and column contracts before collecting data.

- MVP ticker universe.
- MVP event types.
- Article, price, sentiment, event, and training-row columns.

### Step 2: Market-session selection

Implement `src/global_news_market_impact/labels/market_sessions.py` with an exchange calendar.

The first supported cases should be:

- Pre-market article.
- Intraday article.
- After-market article.
- Weekend article.
- U.S. market holiday article.
- Early-close trading day.

Use the actual `XNYS` close. Reject publications in
`[actual_session_close_at_et, actual_session_close_at_et + 1 minute)` instead of selecting a
label date; treat the article as after-market from the end of that window.

The output should provide:

- `previous_confirmed_close_date`.
- `first_regular_session_date`.

### Step 3: Label generation

Implement label generation only after session selection is covered by tests.

The initial label remains:

- `up`: `first_session_adjusted_close > previous_adjusted_close`.
- `not_up`: `first_session_adjusted_close <= previous_adjusted_close`, only after both prices are validated as real,
  finite, and strictly positive.

Missing, non-numeric, boolean, non-finite, or non-positive prices must block label generation.
Keep raw closes for audit and use adjusted closes for label direction. Verify the provider's adjustment method before real-data labeling.

Article preparation validates the minimum `article_id`, `ticker`, and `published_at_et` contract. It rejects missing or duplicate normalized article IDs at table preparation because those errors prevent traceability, while unsupported tickers and invalid publication timestamps remain per-article exclusions. It preserves the original row order and additional source columns for later joins.

The fixture pipeline validates the minimum price contract, rejects duplicate ticker/date rows, selects the article and QQQ/SPY price pairs for the two sessions, and returns either a successful label bundle or a structured exclusion result. Price-related exclusions expose the affected ticker, trading date, and invalid field separately from the human-readable detail.

Batch labeling prepares each source table once and writes successful labels and exclusions to separate stable schemas. Both outputs retain a zero-based input position and `article_id`, so they can be restored to original order or joined to source article text without duplicating text into label-only tables.

Return evaluation uses adjusted-close simple returns. It preserves stock-minus-QQQ and stock-minus-SPY results separately and does not change the initial binary target.

### Step 4: Leakage-safe joins

Feature joins should only use data available before or at `published_at_original`.

Required checks:

- Sentiment joins use normalized `available_at_et`, not only `observed_at_et`; raw schemas preserve the corresponding `*_original` timestamps.
- Event joins use normalized `published_at_et` or `available_at_et`, not only event date; raw schemas preserve the corresponding `*_original` timestamps.
- Same-day close is not used as an input feature.
- Future price movement is used only for labels.

### Step 5: Data feasibility

After the label pipeline shape is stable, evaluate news and price data providers.

The first feasibility result should answer:

- Can we collect enough articles for the 8 MVP tickers?
- Do articles include original publication timestamps?
- Can we distinguish revisions from original publication?
- Can price data and exchange calendars cover holidays and early closes?
