"""Label generation contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

import pandas as pd

from global_news_market_impact.config.tickers import MARKET_BENCHMARK_TICKERS, MVP_TICKERS
from global_news_market_impact.labels.market_sessions import (
    AmbiguousCloseBoundaryError,
    select_label_sessions,
)
from global_news_market_impact.labels.price_rows import (
    PricePair,
    PriceRowErrorReason,
    PriceRowSelectionError,
    select_price_pair,
)
from global_news_market_impact.labels.price_validation import validate_positive_price


@dataclass(frozen=True)
class GeneratedLabel:
    """Initial binary label based on the first regular session after publication."""

    previous_confirmed_close_date: str
    first_regular_session_date: str
    previous_close: float
    first_session_close: float
    previous_adjusted_close: float
    first_session_adjusted_close: float
    label: str


@dataclass(frozen=True)
class ArticleLabelSuccess:
    article_id: str
    ticker: str
    generated_label: GeneratedLabel
    benchmark_price_pairs: tuple[PricePair, ...]


class LabelExclusionReason(StrEnum):
    UNSUPPORTED_TICKER = "UNSUPPORTED_TICKER"
    INVALID_PUBLICATION_TIME = "INVALID_PUBLICATION_TIME"
    AMBIGUOUS_CLOSE_BOUNDARY = "AMBIGUOUS_CLOSE_BOUNDARY"
    INVALID_PRICE_DATA = "INVALID_PRICE_DATA"
    MISSING_PREVIOUS_PRICE = "MISSING_PREVIOUS_PRICE"
    MISSING_FIRST_SESSION_PRICE = "MISSING_FIRST_SESSION_PRICE"
    MISSING_QQQ_PRICE = "MISSING_QQQ_PRICE"
    MISSING_SPY_PRICE = "MISSING_SPY_PRICE"
    DUPLICATE_PRICE_ROW = "DUPLICATE_PRICE_ROW"
    INVALID_PRICE_ROW = "INVALID_PRICE_ROW"


@dataclass(frozen=True)
class ArticleLabelExclusion:
    article_id: str
    ticker: str
    reason: LabelExclusionReason
    detail: str
    previous_confirmed_close_date: str | None = None
    first_regular_session_date: str | None = None


ArticleLabelOutcome = ArticleLabelSuccess | ArticleLabelExclusion


def classify_up_not_up(previous_adjusted_close: float, first_session_adjusted_close: float) -> str:
    """Return the initial MVP label after validating both adjusted closes."""
    validated_previous_adjusted_close = validate_positive_price(
        "previous_adjusted_close", previous_adjusted_close
    )
    validated_first_session_adjusted_close = validate_positive_price(
        "first_session_adjusted_close", first_session_adjusted_close
    )
    return (
        "up"
        if validated_first_session_adjusted_close > validated_previous_adjusted_close
        else "not_up"
    )


def generate_article_label(
    *,
    article_id: str,
    ticker: str,
    published_at_et: datetime,
    price_rows: pd.DataFrame,
) -> ArticleLabelOutcome:
    """Generate one stock label and aligned QQQ/SPY price pairs."""
    normalized_ticker = ticker.strip().upper() if isinstance(ticker, str) else ""
    if normalized_ticker not in MVP_TICKERS:
        return ArticleLabelExclusion(
            article_id=article_id,
            ticker=normalized_ticker,
            reason=LabelExclusionReason.UNSUPPORTED_TICKER,
            detail=f"unsupported prediction ticker: {ticker}",
        )

    try:
        session_selection = select_label_sessions(published_at_et)
    except AmbiguousCloseBoundaryError as error:
        return ArticleLabelExclusion(
            article_id=article_id,
            ticker=normalized_ticker,
            reason=LabelExclusionReason.AMBIGUOUS_CLOSE_BOUNDARY,
            detail=str(error),
        )
    except (TypeError, ValueError) as error:
        return ArticleLabelExclusion(
            article_id=article_id,
            ticker=normalized_ticker,
            reason=LabelExclusionReason.INVALID_PUBLICATION_TIME,
            detail=str(error),
        )

    try:
        stock_price_pair = select_price_pair(
            price_rows,
            ticker=normalized_ticker,
            previous_confirmed_close_date=session_selection.previous_confirmed_close_date,
            first_regular_session_date=session_selection.first_regular_session_date,
        )
        benchmark_price_pairs = tuple(
            select_price_pair(
                price_rows,
                ticker=benchmark_ticker,
                previous_confirmed_close_date=session_selection.previous_confirmed_close_date,
                first_regular_session_date=session_selection.first_regular_session_date,
            )
            for benchmark_ticker in MARKET_BENCHMARK_TICKERS
        )
    except PriceRowSelectionError as error:
        return _price_error_to_exclusion(
            article_id=article_id,
            article_ticker=normalized_ticker,
            error=error,
            previous_confirmed_close_date=session_selection.previous_confirmed_close_date,
            first_regular_session_date=session_selection.first_regular_session_date,
        )

    generated_label = GeneratedLabel(
        previous_confirmed_close_date=session_selection.previous_confirmed_close_date,
        first_regular_session_date=session_selection.first_regular_session_date,
        previous_close=stock_price_pair.previous.close,
        first_session_close=stock_price_pair.first_session.close,
        previous_adjusted_close=stock_price_pair.previous.adjusted_close,
        first_session_adjusted_close=stock_price_pair.first_session.adjusted_close,
        label=classify_up_not_up(
            previous_adjusted_close=stock_price_pair.previous.adjusted_close,
            first_session_adjusted_close=stock_price_pair.first_session.adjusted_close,
        ),
    )
    return ArticleLabelSuccess(
        article_id=article_id,
        ticker=normalized_ticker,
        generated_label=generated_label,
        benchmark_price_pairs=benchmark_price_pairs,
    )


def _price_error_to_exclusion(
    *,
    article_id: str,
    article_ticker: str,
    error: PriceRowSelectionError,
    previous_confirmed_close_date: str,
    first_regular_session_date: str,
) -> ArticleLabelExclusion:
    if error.reason == PriceRowErrorReason.MISSING_PREVIOUS_PRICE:
        reason = _missing_price_reason(
            price_ticker=error.ticker,
            article_ticker=article_ticker,
            stock_reason=LabelExclusionReason.MISSING_PREVIOUS_PRICE,
        )
    elif error.reason == PriceRowErrorReason.MISSING_FIRST_SESSION_PRICE:
        reason = _missing_price_reason(
            price_ticker=error.ticker,
            article_ticker=article_ticker,
            stock_reason=LabelExclusionReason.MISSING_FIRST_SESSION_PRICE,
        )
    elif error.reason == PriceRowErrorReason.DUPLICATE_PRICE_ROW:
        reason = LabelExclusionReason.DUPLICATE_PRICE_ROW
    elif error.reason == PriceRowErrorReason.INVALID_PRICE_ROW:
        reason = LabelExclusionReason.INVALID_PRICE_ROW
    else:
        reason = LabelExclusionReason.INVALID_PRICE_DATA

    return ArticleLabelExclusion(
        article_id=article_id,
        ticker=article_ticker,
        reason=reason,
        detail=str(error),
        previous_confirmed_close_date=previous_confirmed_close_date,
        first_regular_session_date=first_regular_session_date,
    )


def _missing_price_reason(
    *,
    price_ticker: str | None,
    article_ticker: str,
    stock_reason: LabelExclusionReason,
) -> LabelExclusionReason:
    if price_ticker == article_ticker:
        return stock_reason
    if price_ticker == "QQQ":
        return LabelExclusionReason.MISSING_QQQ_PRICE
    if price_ticker == "SPY":
        return LabelExclusionReason.MISSING_SPY_PRICE
    return LabelExclusionReason.INVALID_PRICE_DATA
