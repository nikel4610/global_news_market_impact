from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from global_news_market_impact.labels.generate_labels import (
    ArticleLabelExclusion,
    ArticleLabelSuccess,
    LabelExclusionReason,
    generate_article_label,
)

EASTERN_TIME = ZoneInfo("America/New_York")


def make_price_rows(
    previous_date: str = "2025-06-17",
    first_date: str = "2025-06-18",
) -> pd.DataFrame:
    prices = {
        "NVDA": ((50.0, 100.0), (49.0, 101.0)),
        "QQQ": ((500.0, 500.0), (505.0, 505.0)),
        "SPY": ((600.0, 600.0), (603.0, 603.0)),
    }
    rows: list[dict[str, object]] = []
    for ticker, (previous_prices, first_prices) in prices.items():
        rows.extend(
            [
                {
                    "ticker": ticker,
                    "trading_date": previous_date,
                    "close": previous_prices[0],
                    "adjusted_close": previous_prices[1],
                },
                {
                    "ticker": ticker,
                    "trading_date": first_date,
                    "close": first_prices[0],
                    "adjusted_close": first_prices[1],
                },
            ]
        )
    return pd.DataFrame(rows)


def published_at_et(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int = 0,
) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=EASTERN_TIME)


def test_generate_article_label_uses_adjusted_closes_and_preserves_raw_closes() -> None:
    outcome = generate_article_label(
        article_id="article-1",
        ticker="NVDA",
        published_at_et=published_at_et(2025, 6, 18, 12),
        price_rows=make_price_rows(),
    )

    assert isinstance(outcome, ArticleLabelSuccess)
    assert outcome.generated_label.label == "up"
    assert outcome.generated_label.previous_close == 50.0
    assert outcome.generated_label.first_session_close == 49.0
    assert outcome.generated_label.previous_adjusted_close == 100.0
    assert outcome.generated_label.first_session_adjusted_close == 101.0
    assert tuple(pair.ticker for pair in outcome.benchmark_price_pairs) == ("QQQ", "SPY")
    assert outcome.benchmark_price_pairs[0].first_session.adjusted_close == 505.0
    assert outcome.benchmark_price_pairs[1].first_session.adjusted_close == 603.0
    assert outcome.return_metrics.stock_return == pytest.approx(0.01)
    assert outcome.return_metrics.qqq_return == pytest.approx(0.01)
    assert outcome.return_metrics.spy_return == pytest.approx(0.005)
    assert outcome.return_metrics.excess_return_vs_qqq == pytest.approx(0.0)
    assert outcome.return_metrics.excess_return_vs_spy == pytest.approx(0.005)


@pytest.mark.parametrize(
    ("missing_date", "expected_reason"),
    [
        ("2025-06-17", LabelExclusionReason.MISSING_PREVIOUS_PRICE),
        ("2025-06-18", LabelExclusionReason.MISSING_FIRST_SESSION_PRICE),
    ],
)
def test_generate_article_label_records_missing_stock_session(
    missing_date: str,
    expected_reason: LabelExclusionReason,
) -> None:
    price_rows = make_price_rows().loc[
        lambda rows: ~((rows["ticker"] == "NVDA") & (rows["trading_date"] == missing_date))
    ]

    outcome = generate_article_label(
        article_id="article-1",
        ticker="NVDA",
        published_at_et=published_at_et(2025, 6, 18, 12),
        price_rows=price_rows,
    )

    assert isinstance(outcome, ArticleLabelExclusion)
    assert outcome.reason == expected_reason
    assert outcome.previous_confirmed_close_date == "2025-06-17"
    assert outcome.first_regular_session_date == "2025-06-18"
    assert outcome.price_ticker == "NVDA"
    assert outcome.trading_date == missing_date
    assert outcome.price_field is None


@pytest.mark.parametrize(
    ("benchmark_ticker", "expected_reason"),
    [
        ("QQQ", LabelExclusionReason.MISSING_QQQ_PRICE),
        ("SPY", LabelExclusionReason.MISSING_SPY_PRICE),
    ],
)
def test_generate_article_label_records_missing_benchmark(
    benchmark_ticker: str,
    expected_reason: LabelExclusionReason,
) -> None:
    price_rows = make_price_rows().loc[lambda rows: rows["ticker"] != benchmark_ticker]

    outcome = generate_article_label(
        article_id="article-1",
        ticker="NVDA",
        published_at_et=published_at_et(2025, 6, 18, 12),
        price_rows=price_rows,
    )

    assert isinstance(outcome, ArticleLabelExclusion)
    assert outcome.reason == expected_reason
    assert outcome.price_ticker == benchmark_ticker
    assert outcome.trading_date == "2025-06-17"
    assert outcome.price_field is None


def test_generate_article_label_records_duplicate_price_row() -> None:
    price_rows = pd.concat([make_price_rows(), make_price_rows().iloc[[0]]], ignore_index=True)

    outcome = generate_article_label(
        article_id="article-1",
        ticker="NVDA",
        published_at_et=published_at_et(2025, 6, 18, 12),
        price_rows=price_rows,
    )

    assert isinstance(outcome, ArticleLabelExclusion)
    assert outcome.reason == LabelExclusionReason.DUPLICATE_PRICE_ROW
    assert outcome.price_ticker == "NVDA"
    assert outcome.trading_date == "2025-06-17"
    assert outcome.price_field is None


def test_generate_article_label_ignores_unrelated_duplicate_price_row() -> None:
    unrelated_duplicate = pd.DataFrame(
        [
            {
                "ticker": "AMD",
                "trading_date": "2025-06-17",
                "close": 10.0,
                "adjusted_close": 10.0,
            },
            {
                "ticker": "AMD",
                "trading_date": "2025-06-17",
                "close": 10.0,
                "adjusted_close": 10.0,
            },
        ]
    )
    price_rows = pd.concat([make_price_rows(), unrelated_duplicate], ignore_index=True)

    outcome = generate_article_label(
        article_id="article-1",
        ticker="NVDA",
        published_at_et=published_at_et(2025, 6, 18, 12),
        price_rows=price_rows,
    )

    assert isinstance(outcome, ArticleLabelSuccess)


def test_generate_article_label_records_invalid_adjusted_close() -> None:
    price_rows = make_price_rows()
    price_rows.loc[
        (price_rows["ticker"] == "NVDA") & (price_rows["trading_date"] == "2025-06-17"),
        "adjusted_close",
    ] = float("nan")

    outcome = generate_article_label(
        article_id="article-1",
        ticker="NVDA",
        published_at_et=published_at_et(2025, 6, 18, 12),
        price_rows=price_rows,
    )

    assert isinstance(outcome, ArticleLabelExclusion)
    assert outcome.reason == LabelExclusionReason.INVALID_PRICE_ROW
    assert outcome.price_ticker == "NVDA"
    assert outcome.trading_date == "2025-06-17"
    assert outcome.price_field == "adjusted_close"


def test_generate_article_label_records_ambiguous_close_boundary() -> None:
    outcome = generate_article_label(
        article_id="article-1",
        ticker="NVDA",
        published_at_et=published_at_et(2025, 6, 17, 16),
        price_rows=make_price_rows(),
    )

    assert isinstance(outcome, ArticleLabelExclusion)
    assert outcome.reason == LabelExclusionReason.AMBIGUOUS_CLOSE_BOUNDARY
    assert outcome.previous_confirmed_close_date is None


def test_generate_article_label_rejects_unsupported_ticker() -> None:
    outcome = generate_article_label(
        article_id="article-1",
        ticker="META",
        published_at_et=published_at_et(2025, 6, 18, 12),
        price_rows=make_price_rows(),
    )

    assert isinstance(outcome, ArticleLabelExclusion)
    assert outcome.reason == LabelExclusionReason.UNSUPPORTED_TICKER


def test_generate_article_label_rejects_naive_publication_time() -> None:
    outcome = generate_article_label(
        article_id="article-1",
        ticker="NVDA",
        published_at_et=datetime(2025, 6, 18, 12),  # noqa: DTZ001
        price_rows=make_price_rows(),
    )

    assert isinstance(outcome, ArticleLabelExclusion)
    assert outcome.reason == LabelExclusionReason.INVALID_PUBLICATION_TIME


def test_generate_article_label_rejects_missing_publication_time() -> None:
    outcome = generate_article_label(
        article_id="article-1",
        ticker="NVDA",
        published_at_et=None,  # type: ignore[arg-type]
        price_rows=make_price_rows(),
    )

    assert isinstance(outcome, ArticleLabelExclusion)
    assert outcome.reason == LabelExclusionReason.INVALID_PUBLICATION_TIME


def test_generate_article_label_connects_weekend_to_open_sessions() -> None:
    outcome = generate_article_label(
        article_id="article-weekend",
        ticker="NVDA",
        published_at_et=published_at_et(2025, 6, 21, 12),
        price_rows=make_price_rows(previous_date="2025-06-20", first_date="2025-06-23"),
    )

    assert isinstance(outcome, ArticleLabelSuccess)
    assert outcome.generated_label.previous_confirmed_close_date == "2025-06-20"
    assert outcome.generated_label.first_regular_session_date == "2025-06-23"
