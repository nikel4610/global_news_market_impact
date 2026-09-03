"""Batch article labeling with separate success and exclusion tables."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from global_news_market_impact.config.schema import (
    BATCH_LABEL_EXCLUSION_COLUMNS,
    BATCH_LABEL_SUCCESS_COLUMNS,
)
from global_news_market_impact.data.article_rows import (
    PreparedArticleTable,
    prepare_article_rows,
)
from global_news_market_impact.labels.generate_labels import (
    ArticleLabelExclusion,
    ArticleLabelSuccess,
    generate_article_label,
)
from global_news_market_impact.labels.price_rows import PreparedPriceTable, prepare_price_rows


@dataclass(frozen=True)
class BatchLabelResult:
    """Stable tabular outputs for successful and excluded article labels."""

    success_rows: pd.DataFrame
    exclusion_rows: pd.DataFrame


def generate_article_labels(
    article_rows: pd.DataFrame | PreparedArticleTable,
    price_rows: pd.DataFrame | PreparedPriceTable,
) -> BatchLabelResult:
    """Generate labels in input order while preparing each source table once."""
    prepared_articles = (
        article_rows
        if isinstance(article_rows, PreparedArticleTable)
        else prepare_article_rows(article_rows)
    )
    prepared_prices = (
        price_rows if isinstance(price_rows, PreparedPriceTable) else prepare_price_rows(price_rows)
    )

    success_records: list[dict[str, object]] = []
    exclusion_records: list[dict[str, object]] = []
    for input_position, (_, article_row) in enumerate(prepared_articles.rows.iterrows()):
        outcome = generate_article_label(
            article_id=article_row["article_id"],
            ticker=article_row["ticker"],
            published_at_et=article_row["published_at_et"],
            price_rows=prepared_prices,
        )
        if isinstance(outcome, ArticleLabelSuccess):
            success_records.append(
                _success_record(
                    input_position=input_position,
                    published_at_et=article_row["published_at_et"],
                    outcome=outcome,
                )
            )
        else:
            exclusion_records.append(
                _exclusion_record(
                    input_position=input_position,
                    published_at_et=article_row["published_at_et"],
                    outcome=outcome,
                )
            )

    return BatchLabelResult(
        success_rows=pd.DataFrame.from_records(
            success_records,
            columns=BATCH_LABEL_SUCCESS_COLUMNS,
        ),
        exclusion_rows=pd.DataFrame.from_records(
            exclusion_records,
            columns=BATCH_LABEL_EXCLUSION_COLUMNS,
        ),
    )


def _success_record(
    *,
    input_position: int,
    published_at_et: object,
    outcome: ArticleLabelSuccess,
) -> dict[str, object]:
    label = outcome.generated_label
    returns = outcome.return_metrics
    return {
        "input_position": input_position,
        "article_id": outcome.article_id,
        "ticker": outcome.ticker,
        "published_at_et": published_at_et,
        "previous_confirmed_close_date": label.previous_confirmed_close_date,
        "first_regular_session_date": label.first_regular_session_date,
        "previous_close": label.previous_close,
        "first_session_close": label.first_session_close,
        "previous_adjusted_close": label.previous_adjusted_close,
        "first_session_adjusted_close": label.first_session_adjusted_close,
        "label": label.label,
        "stock_return": returns.stock_return,
        "qqq_return": returns.qqq_return,
        "spy_return": returns.spy_return,
        "excess_return_vs_qqq": returns.excess_return_vs_qqq,
        "excess_return_vs_spy": returns.excess_return_vs_spy,
    }


def _exclusion_record(
    *,
    input_position: int,
    published_at_et: object,
    outcome: ArticleLabelExclusion,
) -> dict[str, object]:
    return {
        "input_position": input_position,
        "article_id": outcome.article_id,
        "ticker": outcome.ticker,
        "published_at_et": published_at_et,
        "reason": outcome.reason.value,
        "detail": outcome.detail,
        "previous_confirmed_close_date": outcome.previous_confirmed_close_date,
        "first_regular_session_date": outcome.first_regular_session_date,
        "price_ticker": outcome.price_ticker,
        "trading_date": outcome.trading_date,
        "price_field": outcome.price_field,
    }
