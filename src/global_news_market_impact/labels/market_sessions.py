"""Select price dates from official U.S. regular-session boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import exchange_calendars as xcals

EASTERN_TIME = ZoneInfo("America/New_York")
MARKET_CALENDAR_START_DATE = "2020-01-01"
MARKET_CALENDAR_END_DATE = "2030-12-31"
NYSE_CALENDAR = xcals.get_calendar(
    "XNYS",
    start=MARKET_CALENDAR_START_DATE,
    end=MARKET_CALENDAR_END_DATE,
)
# Conservative MVP fallback until each price provider's close availability is known.
CLOSE_CONFIRMATION_FALLBACK_WINDOW = timedelta(minutes=1)


class AmbiguousCloseBoundaryError(ValueError):
    """Raised when publication falls inside the close-confirmation fallback window."""


@dataclass(frozen=True)
class LabelSessionSelection:
    """Dates needed to generate the initial up/not_up label."""

    previous_confirmed_close_date: str
    first_regular_session_date: str


def select_label_sessions(published_at_et: datetime) -> LabelSessionSelection:
    """Select the last confirmed close and first regular session after publication.

    The NYSE calendar supplies both trading dates and the actual session bounds,
    including holidays and early closes. Publications in the one-minute fallback
    window starting at the scheduled close are rejected until provider-specific
    close availability can replace this conservative MVP rule.
    """
    if published_at_et.tzinfo is None or published_at_et.utcoffset() is None:
        raise ValueError("published_at_et must be timezone-aware")

    published_at_et = published_at_et.astimezone(EASTERN_TIME)
    published_date = published_at_et.date()

    if NYSE_CALENDAR.is_session(published_date):
        session_date = NYSE_CALENDAR.date_to_session(published_date)
        regular_session_open_at_et = NYSE_CALENDAR.session_open(session_date).tz_convert(
            EASTERN_TIME
        )
        actual_session_close_at_et = NYSE_CALENDAR.session_close(session_date).tz_convert(
            EASTERN_TIME
        )
        close_confirmation_fallback_end_at_et = (
            actual_session_close_at_et + CLOSE_CONFIRMATION_FALLBACK_WINDOW
        )

        is_pre_market = published_at_et < regular_session_open_at_et
        is_intraday = regular_session_open_at_et <= published_at_et < actual_session_close_at_et
        is_ambiguous_close_boundary = (
            actual_session_close_at_et <= published_at_et < close_confirmation_fallback_end_at_et
        )

        if is_ambiguous_close_boundary:
            raise AmbiguousCloseBoundaryError(
                "published_at_et falls within the one-minute close-confirmation fallback window"
            )

        if is_pre_market or is_intraday:
            previous_close_session = NYSE_CALENDAR.previous_session(session_date)
            first_regular_session = session_date
        else:
            previous_close_session = session_date
            first_regular_session = NYSE_CALENDAR.next_session(session_date)
    else:
        previous_close_session = NYSE_CALENDAR.date_to_session(published_date, direction="previous")
        first_regular_session = NYSE_CALENDAR.date_to_session(published_date, direction="next")

    return LabelSessionSelection(
        previous_confirmed_close_date=previous_close_session.date().isoformat(),
        first_regular_session_date=first_regular_session.date().isoformat(),
    )
