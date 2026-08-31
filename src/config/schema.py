"""Column names for MVP tabular datasets.

Timestamp columns ending in ``_original`` preserve the provider value and its
source timezone. Corresponding ``_et`` columns store the normalized U.S.
Eastern Time value. ``trading_date`` is a market-session date, not a timestamp.
"""

ARTICLE_COLUMNS: tuple[str, ...] = (
    "article_id",
    "title",
    "summary",
    "published_at_original",
    "published_at_et",
    "source",
    "url",
    "ticker",
)

PRICE_COLUMNS: tuple[str, ...] = (
    "ticker",
    "trading_date",
    "open",
    "high",
    "low",
    "close",
    "adjusted_close",
    "volume",
)

SENTIMENT_COLUMNS: tuple[str, ...] = (
    "sentiment_id",
    "observed_at_original",
    "observed_at_et",
    "available_at_original",
    "available_at_et",
    "sentiment_value",
    "sentiment_source",
)

EVENT_COLUMNS: tuple[str, ...] = (
    "event_id",
    "event_type",
    "published_at_original",
    "published_at_et",
    "available_at_original",
    "available_at_et",
    "source",
    "title",
    "importance",
)

# Stored for identification, traceability, and evaluation only. Never model features.
# The published_at columns here refer to the article, not sentiment or event source rows.
AUDIT_IDENTIFIER_COLUMNS: tuple[str, ...] = (
    "article_id",
    "ticker",
    "published_at_original",
    "published_at_et",
    "sentiment_available_at_et",
    "event_window_start",
    "event_window_end",
    "previous_confirmed_close_date",
    "first_regular_session_date",
)

NEWS_TEXT_FEATURE_COLUMNS: tuple[str, ...] = (
    "title",
    "summary",
)

SENTIMENT_FEATURE_COLUMNS: tuple[str, ...] = ("sentiment_value",)

EVENT_FEATURE_COLUMNS: tuple[str, ...] = (
    "has_tariff_policy_event",
    "has_fomc_event",
    "has_cpi_event",
    "has_employment_event",
)

NEWS_ONLY_FEATURE_COLUMNS: tuple[str, ...] = NEWS_TEXT_FEATURE_COLUMNS
NEWS_SENTIMENT_FEATURE_COLUMNS: tuple[str, ...] = (
    NEWS_ONLY_FEATURE_COLUMNS + SENTIMENT_FEATURE_COLUMNS
)
NEWS_SENTIMENT_EVENT_FEATURE_COLUMNS: tuple[str, ...] = (
    NEWS_SENTIMENT_FEATURE_COLUMNS + EVENT_FEATURE_COLUMNS
)

LABEL_GENERATION_COLUMNS: tuple[str, ...] = (
    "previous_close",
    "first_session_close",
)

TARGET_COLUMNS: tuple[str, ...] = ("label",)

# Complete persisted and auditable row schema. Never pass this tuple directly to a model.
TRAINING_ROW_COLUMNS: tuple[str, ...] = (
    "article_id",
    "ticker",
    "title",
    "summary",
    "published_at_original",
    "published_at_et",
    "sentiment_available_at_et",
    "sentiment_value",
    "event_window_start",
    "event_window_end",
    "has_tariff_policy_event",
    "has_fomc_event",
    "has_cpi_event",
    "has_employment_event",
    "previous_confirmed_close_date",
    "first_regular_session_date",
    "previous_close",
    "first_session_close",
    "label",
)
