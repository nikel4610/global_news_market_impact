from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from global_news_market_impact.config.schema import (
    BATCH_LABEL_EXCLUSION_COLUMNS,
    BATCH_LABEL_SUCCESS_COLUMNS,
)
from global_news_market_impact.labels.batch import BatchLabelResult, generate_article_labels

EASTERN_TIME = ZoneInfo("America/New_York")


def make_article_rows() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "article_id": "article-success",
                "ticker": "nvda",
                "published_at_et": datetime(2025, 6, 18, 12, tzinfo=EASTERN_TIME),
            },
            {
                "article_id": "article-unsupported",
                "ticker": "META",
                "published_at_et": datetime(2025, 6, 18, 12, tzinfo=EASTERN_TIME),
            },
            {
                "article_id": "article-missing-price",
                "ticker": "AMD",
                "published_at_et": datetime(2025, 6, 18, 12, tzinfo=EASTERN_TIME),
            },
            {
                "article_id": "article-invalid-time",
                "ticker": "NVDA",
                "published_at_et": "2025-06-18T12:00:00-04:00",
            },
        ]
    )


def make_price_rows() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    prices = {
        "NVDA": (100.0, 101.0),
        "QQQ": (500.0, 505.0),
        "SPY": (600.0, 603.0),
    }
    for ticker, (previous_close, first_close) in prices.items():
        rows.extend(
            [
                {
                    "ticker": ticker,
                    "trading_date": "2025-06-17",
                    "close": previous_close,
                    "adjusted_close": previous_close,
                },
                {
                    "ticker": ticker,
                    "trading_date": "2025-06-18",
                    "close": first_close,
                    "adjusted_close": first_close,
                },
            ]
        )
    return pd.DataFrame(rows)


def test_batch_labels_separate_successes_and_exclusions_in_input_order() -> None:
    result = generate_article_labels(make_article_rows(), make_price_rows())

    assert isinstance(result, BatchLabelResult)
    assert tuple(result.success_rows.columns) == BATCH_LABEL_SUCCESS_COLUMNS
    assert result.success_rows["input_position"].tolist() == [0]
    assert result.success_rows["article_id"].tolist() == ["article-success"]
    assert result.success_rows["ticker"].tolist() == ["NVDA"]
    assert result.success_rows["label"].tolist() == ["up"]
    assert result.success_rows.loc[0, "stock_return"] == pytest.approx(0.01)

    assert tuple(result.exclusion_rows.columns) == BATCH_LABEL_EXCLUSION_COLUMNS
    assert result.exclusion_rows["input_position"].tolist() == [1, 2, 3]
    assert result.exclusion_rows["article_id"].tolist() == [
        "article-unsupported",
        "article-missing-price",
        "article-invalid-time",
    ]
    assert result.exclusion_rows["reason"].tolist() == [
        "UNSUPPORTED_TICKER",
        "MISSING_PREVIOUS_PRICE",
        "INVALID_PUBLICATION_TIME",
    ]
    assert result.exclusion_rows.loc[1, "price_ticker"] == "AMD"
    assert result.exclusion_rows.loc[1, "trading_date"] == "2025-06-17"


def test_batch_labels_return_stable_empty_output_tables() -> None:
    empty_articles = pd.DataFrame(columns=["article_id", "ticker", "published_at_et"])

    result = generate_article_labels(empty_articles, make_price_rows())

    assert result.success_rows.empty
    assert tuple(result.success_rows.columns) == BATCH_LABEL_SUCCESS_COLUMNS
    assert result.exclusion_rows.empty
    assert tuple(result.exclusion_rows.columns) == BATCH_LABEL_EXCLUSION_COLUMNS


def test_batch_labels_preserve_structured_invalid_price_details() -> None:
    article_rows = make_article_rows().iloc[[0]]
    price_rows = make_price_rows()
    price_rows.loc[
        (price_rows["ticker"] == "NVDA") & (price_rows["trading_date"] == "2025-06-17"),
        "adjusted_close",
    ] = float("nan")

    result = generate_article_labels(article_rows, price_rows)

    assert result.success_rows.empty
    assert result.exclusion_rows.loc[0, "reason"] == "INVALID_PRICE_ROW"
    assert result.exclusion_rows.loc[0, "price_ticker"] == "NVDA"
    assert result.exclusion_rows.loc[0, "trading_date"] == "2025-06-17"
    assert result.exclusion_rows.loc[0, "price_field"] == "adjusted_close"


def test_batch_labels_prepare_price_rows_once(monkeypatch) -> None:
    from global_news_market_impact.labels import batch

    prepare_calls = 0
    original_prepare_price_rows = batch.prepare_price_rows

    def counting_prepare_price_rows(price_rows: pd.DataFrame):
        nonlocal prepare_calls
        prepare_calls += 1
        return original_prepare_price_rows(price_rows)

    monkeypatch.setattr(batch, "prepare_price_rows", counting_prepare_price_rows)

    generate_article_labels(make_article_rows(), make_price_rows())

    assert prepare_calls == 1
