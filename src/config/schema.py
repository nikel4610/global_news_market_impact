"""Column names for MVP tabular datasets."""

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
    "observed_at",
    "available_at",
    "sentiment_value",
    "sentiment_source",
)

EVENT_COLUMNS: tuple[str, ...] = (
    "event_id",
    "event_type",
    "published_at_original",
    "published_at_et",
    "available_at_et",
    "source",
    "title",
    "importance",
)

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

