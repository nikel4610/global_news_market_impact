from datetime import date, datetime

import pandas as pd
import pytest

from global_news_market_impact.labels.price_rows import (
    PriceRowErrorReason,
    PriceRowSelectionError,
    select_price_pair,
)


def make_price_rows() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "ticker": "nvda",
                "trading_date": "2025-06-17",
                "close": 50.0,
                "adjusted_close": 100.0,
            },
            {
                "ticker": "NVDA",
                "trading_date": date(2025, 6, 18),
                "close": 51.0,
                "adjusted_close": 101.0,
            },
        ]
    )


def test_select_price_pair_normalizes_ticker_and_supported_date_types() -> None:
    pair = select_price_pair(
        make_price_rows(),
        ticker=" nvda ",
        previous_confirmed_close_date="2025-06-17",
        first_regular_session_date="2025-06-18",
    )

    assert pair.ticker == "NVDA"
    assert pair.previous.trading_date == "2025-06-17"
    assert pair.previous.close == 50.0
    assert pair.previous.adjusted_close == 100.0
    assert pair.first_session.trading_date == "2025-06-18"
    assert pair.first_session.adjusted_close == 101.0


def test_price_rows_require_all_label_price_columns() -> None:
    price_rows = make_price_rows().drop(columns="adjusted_close")

    with pytest.raises(PriceRowSelectionError) as error_info:
        select_price_pair(
            price_rows,
            ticker="NVDA",
            previous_confirmed_close_date="2025-06-17",
            first_regular_session_date="2025-06-18",
        )

    assert error_info.value.reason == PriceRowErrorReason.INVALID_SCHEMA
    assert "adjusted_close" in str(error_info.value)


def test_price_rows_reject_duplicate_ticker_and_date() -> None:
    price_rows = pd.concat([make_price_rows(), make_price_rows().iloc[[0]]], ignore_index=True)

    with pytest.raises(PriceRowSelectionError) as error_info:
        select_price_pair(
            price_rows,
            ticker="NVDA",
            previous_confirmed_close_date="2025-06-17",
            first_regular_session_date="2025-06-18",
        )

    assert error_info.value.reason == PriceRowErrorReason.DUPLICATE_PRICE_ROW
    assert error_info.value.ticker == "NVDA"
    assert error_info.value.trading_date == "2025-06-17"


def test_price_rows_reject_non_midnight_datetime() -> None:
    price_rows = make_price_rows()
    price_rows.loc[0, "trading_date"] = datetime(2025, 6, 17, 12)  # noqa: DTZ001

    with pytest.raises(PriceRowSelectionError) as error_info:
        select_price_pair(
            price_rows,
            ticker="NVDA",
            previous_confirmed_close_date="2025-06-17",
            first_regular_session_date="2025-06-18",
        )

    assert error_info.value.reason == PriceRowErrorReason.INVALID_TRADING_DATE


@pytest.mark.parametrize(
    ("missing_date", "expected_reason"),
    [
        ("2025-06-17", PriceRowErrorReason.MISSING_PREVIOUS_PRICE),
        ("2025-06-18", PriceRowErrorReason.MISSING_FIRST_SESSION_PRICE),
    ],
)
def test_price_pair_reports_which_session_is_missing(
    missing_date: str,
    expected_reason: PriceRowErrorReason,
) -> None:
    price_rows = make_price_rows().loc[
        lambda rows: rows["trading_date"].astype(str) != missing_date
    ]

    with pytest.raises(PriceRowSelectionError) as error_info:
        select_price_pair(
            price_rows,
            ticker="NVDA",
            previous_confirmed_close_date="2025-06-17",
            first_regular_session_date="2025-06-18",
        )

    assert error_info.value.reason == expected_reason


@pytest.mark.parametrize("column", ["close", "adjusted_close"])
def test_selected_price_row_rejects_invalid_raw_or_adjusted_close(column: str) -> None:
    price_rows = make_price_rows()
    price_rows.loc[0, column] = float("nan")

    with pytest.raises(PriceRowSelectionError) as error_info:
        select_price_pair(
            price_rows,
            ticker="NVDA",
            previous_confirmed_close_date="2025-06-17",
            first_regular_session_date="2025-06-18",
        )

    assert error_info.value.reason == PriceRowErrorReason.INVALID_PRICE_ROW
    assert column in str(error_info.value)
