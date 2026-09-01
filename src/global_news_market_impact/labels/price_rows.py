"""Validate daily price rows and select the two sessions used for a label."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from enum import StrEnum

import pandas as pd

from global_news_market_impact.labels.price_validation import (
    InvalidLabelPriceError,
    validate_positive_price,
)

REQUIRED_LABEL_PRICE_COLUMNS: tuple[str, ...] = (
    "ticker",
    "trading_date",
    "close",
    "adjusted_close",
)


class PriceRowErrorReason(StrEnum):
    INVALID_SCHEMA = "INVALID_SCHEMA"
    INVALID_TRADING_DATE = "INVALID_TRADING_DATE"
    DUPLICATE_PRICE_ROW = "DUPLICATE_PRICE_ROW"
    MISSING_PREVIOUS_PRICE = "MISSING_PREVIOUS_PRICE"
    MISSING_FIRST_SESSION_PRICE = "MISSING_FIRST_SESSION_PRICE"
    INVALID_PRICE_ROW = "INVALID_PRICE_ROW"


class PriceRowSelectionError(ValueError):
    """Raised when daily price rows cannot produce an unambiguous price pair."""

    def __init__(
        self,
        reason: PriceRowErrorReason,
        detail: str,
        *,
        ticker: str | None = None,
        trading_date: str | None = None,
    ) -> None:
        self.reason = reason
        self.ticker = ticker
        self.trading_date = trading_date
        super().__init__(detail)


@dataclass(frozen=True)
class PriceObservation:
    trading_date: str
    close: float
    adjusted_close: float


@dataclass(frozen=True)
class PricePair:
    ticker: str
    previous: PriceObservation
    first_session: PriceObservation


def select_price_pair(
    price_rows: pd.DataFrame,
    *,
    ticker: str,
    previous_confirmed_close_date: str,
    first_regular_session_date: str,
) -> PricePair:
    """Select one validated price row for each label session."""
    normalized_rows = _normalize_price_rows(price_rows)
    normalized_ticker = _normalize_ticker(ticker)
    previous_date = _normalize_target_date(previous_confirmed_close_date)
    first_date = _normalize_target_date(first_regular_session_date)

    previous = _select_observation(
        normalized_rows,
        ticker=normalized_ticker,
        trading_date=previous_date,
        missing_reason=PriceRowErrorReason.MISSING_PREVIOUS_PRICE,
    )
    first_session = _select_observation(
        normalized_rows,
        ticker=normalized_ticker,
        trading_date=first_date,
        missing_reason=PriceRowErrorReason.MISSING_FIRST_SESSION_PRICE,
    )
    return PricePair(
        ticker=normalized_ticker,
        previous=previous,
        first_session=first_session,
    )


def _normalize_price_rows(price_rows: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(price_rows, pd.DataFrame):
        raise PriceRowSelectionError(
            PriceRowErrorReason.INVALID_SCHEMA,
            "price_rows must be a pandas DataFrame",
        )

    missing_columns = sorted(set(REQUIRED_LABEL_PRICE_COLUMNS) - set(price_rows.columns))
    if missing_columns:
        raise PriceRowSelectionError(
            PriceRowErrorReason.INVALID_SCHEMA,
            f"price_rows is missing required columns: {', '.join(missing_columns)}",
        )

    normalized_rows = price_rows.loc[:, REQUIRED_LABEL_PRICE_COLUMNS].copy()
    normalized_rows["ticker"] = normalized_rows["ticker"].map(_normalize_ticker)
    normalized_rows["trading_date"] = normalized_rows["trading_date"].map(_normalize_trading_date)

    duplicate_mask = normalized_rows.duplicated(subset=["ticker", "trading_date"], keep=False)
    if duplicate_mask.any():
        duplicate_row = normalized_rows.loc[duplicate_mask].iloc[0]
        duplicate_date = duplicate_row["trading_date"].isoformat()
        duplicate_ticker = str(duplicate_row["ticker"])
        raise PriceRowSelectionError(
            PriceRowErrorReason.DUPLICATE_PRICE_ROW,
            f"duplicate price row for {duplicate_ticker} on {duplicate_date}",
            ticker=duplicate_ticker,
            trading_date=duplicate_date,
        )

    return normalized_rows


def _normalize_ticker(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PriceRowSelectionError(
            PriceRowErrorReason.INVALID_SCHEMA,
            "ticker must be a non-empty string",
        )
    return value.strip().upper()


def _normalize_trading_date(value: object) -> date:
    if isinstance(value, pd.Timestamp):
        value = value.to_pydatetime()

    if isinstance(value, datetime):
        if value.timetz().replace(tzinfo=None) != time.min:
            raise PriceRowSelectionError(
                PriceRowErrorReason.INVALID_TRADING_DATE,
                "trading_date datetime must be at midnight",
            )
        return value.date()

    if isinstance(value, date):
        return value

    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError as error:
            raise PriceRowSelectionError(
                PriceRowErrorReason.INVALID_TRADING_DATE,
                f"invalid trading_date: {value}",
            ) from error

    raise PriceRowSelectionError(
        PriceRowErrorReason.INVALID_TRADING_DATE,
        "trading_date must be an ISO date, date, or midnight datetime",
    )


def _normalize_target_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as error:
        raise PriceRowSelectionError(
            PriceRowErrorReason.INVALID_TRADING_DATE,
            f"invalid target trading date: {value}",
        ) from error


def _select_observation(
    normalized_rows: pd.DataFrame,
    *,
    ticker: str,
    trading_date: date,
    missing_reason: PriceRowErrorReason,
) -> PriceObservation:
    matching_rows = normalized_rows.loc[
        (normalized_rows["ticker"] == ticker) & (normalized_rows["trading_date"] == trading_date)
    ]
    trading_date_text = trading_date.isoformat()

    if matching_rows.empty:
        raise PriceRowSelectionError(
            missing_reason,
            f"missing {ticker} price row for {trading_date_text}",
            ticker=ticker,
            trading_date=trading_date_text,
        )

    row = matching_rows.iloc[0]
    try:
        close = validate_positive_price("close", row["close"])
        adjusted_close = validate_positive_price("adjusted_close", row["adjusted_close"])
    except InvalidLabelPriceError as error:
        raise PriceRowSelectionError(
            PriceRowErrorReason.INVALID_PRICE_ROW,
            f"invalid {ticker} price row for {trading_date_text}: {error}",
            ticker=ticker,
            trading_date=trading_date_text,
        ) from error

    return PriceObservation(
        trading_date=trading_date_text,
        close=close,
        adjusted_close=adjusted_close,
    )
