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

- Use only the MVP tickers defined in `src/config/tickers.py`.
- Use only the MVP event types defined in `src/config/events.py`.
- Normalize analysis timestamps to U.S. Eastern Time.
- Use an exchange calendar for U.S. market holidays and early closes.
- Compare exact timestamps, not only dates.
- Do not use data that was unavailable at `published_at_original`.

## Initial Implementation Plan

### Step 1: Schema and constants

Create the stable MVP constants and column contracts before collecting data.

- MVP ticker universe.
- MVP event types.
- Article, price, sentiment, event, and training-row columns.

### Step 2: Market-session selection

Implement `src/labels/market_sessions.py` with an exchange calendar.

The first supported cases should be:

- Intraday article.
- After-market article.
- Weekend article.
- U.S. market holiday article.
- Early-close trading day.

The output should provide:

- `previous_confirmed_close_date`.
- `first_regular_session_date`.

### Step 3: Label generation

Implement label generation only after session selection is covered by tests.

The initial label remains:

- `up`: `first_session_close > previous_close`.
- `not_up`: otherwise.

### Step 4: Leakage-safe joins

Feature joins should only use data available before or at `published_at_original`.

Required checks:

- Sentiment uses `available_at`, not only `observed_at`.
- Events use `published_at` or `available_at`, not only event date.
- Same-day close is not used as an input feature.
- Future price movement is used only for labels.

### Step 5: Data feasibility

After the label pipeline shape is stable, evaluate news and price data providers.

The first feasibility result should answer:

- Can we collect enough articles for the 8 MVP tickers?
- Do articles include original publication timestamps?
- Can we distinguish revisions from original publication?
- Can price data and exchange calendars cover holidays and early closes?
