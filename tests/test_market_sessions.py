from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from global_news_market_impact.labels.market_sessions import (
    MARKET_CALENDAR_END_DATE,
    MARKET_CALENDAR_START_DATE,
    NYSE_CALENDAR,
    AmbiguousCloseBoundaryError,
    LabelSessionSelection,
    select_label_sessions,
)

EASTERN_TIME = ZoneInfo("America/New_York")


def test_market_calendar_has_explicit_mvp_bounds() -> None:
    assert MARKET_CALENDAR_START_DATE == "2020-01-01"
    assert MARKET_CALENDAR_END_DATE == "2030-12-31"
    assert NYSE_CALENDAR.first_session.date().isoformat() == "2020-01-02"
    assert NYSE_CALENDAR.last_session.date().isoformat() == "2030-12-31"


def published_at_et(
    year: int, month: int, day: int, hour: int, minute: int = 0, second: int = 0
) -> datetime:
    return datetime(year, month, day, hour, minute, second, tzinfo=EASTERN_TIME)


def test_intraday_article_does_not_use_unconfirmed_same_day_close_as_previous_close() -> None:
    selection = select_label_sessions(published_at_et(2025, 6, 18, 12))

    assert selection == LabelSessionSelection(
        previous_confirmed_close_date="2025-06-17",
        first_regular_session_date="2025-06-18",
    )


def test_after_market_article_uses_confirmed_same_day_close_without_future_leakage() -> None:
    selection = select_label_sessions(published_at_et(2025, 6, 17, 16, 30))

    assert selection == LabelSessionSelection(
        previous_confirmed_close_date="2025-06-17",
        first_regular_session_date="2025-06-18",
    )


def test_regular_session_just_before_close_remains_intraday() -> None:
    selection = select_label_sessions(published_at_et(2025, 6, 17, 15, 59, 59))

    assert selection == LabelSessionSelection(
        previous_confirmed_close_date="2025-06-16",
        first_regular_session_date="2025-06-17",
    )


@pytest.mark.parametrize("second", [0, 59])
def test_regular_close_fallback_window_blocks_ambiguous_label_dates(second: int) -> None:
    with pytest.raises(AmbiguousCloseBoundaryError, match="close-confirmation"):
        select_label_sessions(published_at_et(2025, 6, 17, 16, 0, second))


def test_regular_session_one_minute_after_close_is_after_market() -> None:
    selection = select_label_sessions(published_at_et(2025, 6, 17, 16, 1))

    assert selection == LabelSessionSelection(
        previous_confirmed_close_date="2025-06-17",
        first_regular_session_date="2025-06-18",
    )


def test_weekend_article_brackets_publication_with_open_sessions() -> None:
    selection = select_label_sessions(published_at_et(2025, 6, 21, 12))

    assert selection == LabelSessionSelection(
        previous_confirmed_close_date="2025-06-20",
        first_regular_session_date="2025-06-23",
    )


def test_us_market_holiday_article_does_not_join_to_non_trading_date() -> None:
    selection = select_label_sessions(published_at_et(2025, 7, 4, 12))

    assert selection == LabelSessionSelection(
        previous_confirmed_close_date="2025-07-03",
        first_regular_session_date="2025-07-07",
    )


def test_early_close_article_uses_actual_close_instead_of_fixed_1600_cutoff() -> None:
    selection = select_label_sessions(published_at_et(2025, 7, 3, 13, 30))

    assert selection == LabelSessionSelection(
        previous_confirmed_close_date="2025-07-03",
        first_regular_session_date="2025-07-07",
    )


@pytest.mark.parametrize("second", [0, 59])
def test_early_close_fallback_window_blocks_ambiguous_label_dates(second: int) -> None:
    with pytest.raises(AmbiguousCloseBoundaryError, match="close-confirmation"):
        select_label_sessions(published_at_et(2025, 7, 3, 13, 0, second))


def test_early_close_one_minute_after_close_is_after_market() -> None:
    selection = select_label_sessions(published_at_et(2025, 7, 3, 13, 1))

    assert selection == LabelSessionSelection(
        previous_confirmed_close_date="2025-07-03",
        first_regular_session_date="2025-07-07",
    )


def test_naive_publication_timestamp_is_rejected() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        select_label_sessions(datetime(2025, 6, 18, 12, tzinfo=None))  # noqa: DTZ001
