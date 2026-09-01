import pytest

from global_news_market_impact.config.schema import (
    ARTICLE_COLUMNS,
    AUDIT_IDENTIFIER_COLUMNS,
    EVENT_COLUMNS,
    EVENT_FEATURE_COLUMNS,
    LABEL_GENERATION_COLUMNS,
    LABEL_PRICE_AUDIT_COLUMNS,
    NEWS_ONLY_FEATURE_COLUMNS,
    NEWS_SENTIMENT_EVENT_FEATURE_COLUMNS,
    NEWS_SENTIMENT_FEATURE_COLUMNS,
    NEWS_TEXT_FEATURE_COLUMNS,
    RETURN_EVALUATION_COLUMNS,
    SENTIMENT_COLUMNS,
    SENTIMENT_FEATURE_COLUMNS,
    TARGET_COLUMNS,
    TRAINING_ROW_COLUMNS,
)

EXPERIMENT_FEATURE_GROUPS = (
    NEWS_ONLY_FEATURE_COLUMNS,
    NEWS_SENTIMENT_FEATURE_COLUMNS,
    NEWS_SENTIMENT_EVENT_FEATURE_COLUMNS,
)

ALL_COLUMN_GROUPS = (
    AUDIT_IDENTIFIER_COLUMNS,
    NEWS_TEXT_FEATURE_COLUMNS,
    SENTIMENT_FEATURE_COLUMNS,
    EVENT_FEATURE_COLUMNS,
    *EXPERIMENT_FEATURE_GROUPS,
    LABEL_PRICE_AUDIT_COLUMNS,
    LABEL_GENERATION_COLUMNS,
    RETURN_EVALUATION_COLUMNS,
    TARGET_COLUMNS,
    TRAINING_ROW_COLUMNS,
)

SOURCE_SCHEMA_TIMESTAMP_PAIRS = (
    (ARTICLE_COLUMNS, {"published_at_original", "published_at_et"}),
    (
        SENTIMENT_COLUMNS,
        {
            "observed_at_original",
            "observed_at_et",
            "available_at_original",
            "available_at_et",
        },
    ),
    (
        EVENT_COLUMNS,
        {
            "published_at_original",
            "published_at_et",
            "available_at_original",
            "available_at_et",
        },
    ),
)

SOURCE_ONLY_SENTIMENT_EVENT_TIMESTAMPS = {
    "observed_at_original",
    "observed_at_et",
    "available_at_original",
    "available_at_et",
}


@pytest.mark.parametrize(("source_columns", "required_timestamps"), SOURCE_SCHEMA_TIMESTAMP_PAIRS)
def test_source_schemas_preserve_original_and_eastern_timestamp_pairs(
    source_columns: tuple[str, ...], required_timestamps: set[str]
) -> None:
    assert required_timestamps.issubset(source_columns)


def test_source_schemas_do_not_keep_ambiguous_standalone_timestamp_names() -> None:
    ambiguous_timestamp_names = {"observed_at", "available_at"}

    for source_columns, _ in SOURCE_SCHEMA_TIMESTAMP_PAIRS:
        assert ambiguous_timestamp_names.isdisjoint(source_columns)


def test_training_row_uses_only_normalized_sentiment_event_join_timestamps() -> None:
    assert "sentiment_available_at_et" in TRAINING_ROW_COLUMNS
    assert SOURCE_ONLY_SENTIMENT_EVENT_TIMESTAMPS.isdisjoint(TRAINING_ROW_COLUMNS)
    assert {"published_at_original", "published_at_et"}.issubset(AUDIT_IDENTIFIER_COLUMNS)


@pytest.mark.parametrize("feature_columns", EXPERIMENT_FEATURE_GROUPS)
def test_model_features_exclude_all_source_timestamps(feature_columns: tuple[str, ...]) -> None:
    all_source_timestamps = set().union(
        *(required_timestamps for _, required_timestamps in SOURCE_SCHEMA_TIMESTAMP_PAIRS)
    )

    assert all_source_timestamps.isdisjoint(feature_columns)
    assert "sentiment_available_at_et" not in feature_columns


@pytest.mark.parametrize("feature_columns", EXPERIMENT_FEATURE_GROUPS)
def test_model_features_exclude_future_prices_and_target(
    feature_columns: tuple[str, ...],
) -> None:
    forbidden_future_columns = {
        *LABEL_PRICE_AUDIT_COLUMNS,
        *LABEL_GENERATION_COLUMNS,
        *RETURN_EVALUATION_COLUMNS,
        *TARGET_COLUMNS,
    }

    assert forbidden_future_columns.isdisjoint(feature_columns)


@pytest.mark.parametrize("feature_columns", EXPERIMENT_FEATURE_GROUPS)
def test_model_features_exclude_audit_identifiers_and_ticker(
    feature_columns: tuple[str, ...],
) -> None:
    assert "ticker" in AUDIT_IDENTIFIER_COLUMNS
    assert set(AUDIT_IDENTIFIER_COLUMNS).isdisjoint(feature_columns)


def test_experiment_features_accumulate_in_declared_order() -> None:
    assert NEWS_SENTIMENT_FEATURE_COLUMNS == (NEWS_ONLY_FEATURE_COLUMNS + SENTIMENT_FEATURE_COLUMNS)
    assert NEWS_SENTIMENT_EVENT_FEATURE_COLUMNS == (
        NEWS_SENTIMENT_FEATURE_COLUMNS + EVENT_FEATURE_COLUMNS
    )


@pytest.mark.parametrize("column_group", ALL_COLUMN_GROUPS)
def test_schema_column_groups_do_not_contain_duplicates(column_group: tuple[str, ...]) -> None:
    assert len(column_group) == len(set(column_group))


def test_full_training_row_contains_every_declared_column_group() -> None:
    classified_training_columns = {
        *AUDIT_IDENTIFIER_COLUMNS,
        *NEWS_SENTIMENT_EVENT_FEATURE_COLUMNS,
        *LABEL_PRICE_AUDIT_COLUMNS,
        *LABEL_GENERATION_COLUMNS,
        *RETURN_EVALUATION_COLUMNS,
        *TARGET_COLUMNS,
    }

    assert classified_training_columns == set(TRAINING_ROW_COLUMNS)
