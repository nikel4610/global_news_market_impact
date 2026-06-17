"""Market-session selection contracts.

Implementation starts here after the initial project structure is reviewed.
The functions in this module must use an exchange calendar and U.S. Eastern
Time. They must not classify sessions with naive date-only logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class LabelSessionSelection:
    """Dates needed to generate the initial up/not_up label."""

    previous_confirmed_close_date: str
    first_regular_session_date: str


def select_label_sessions(published_at_et: datetime) -> LabelSessionSelection:
    """Select close dates for label generation.

    This is intentionally not implemented in the structure pass. The next step
    is to implement it with exchange-calendars and tests for intraday,
    after-market, weekend, holiday, and early-close articles.
    """
    raise NotImplementedError("Implement with an exchange calendar before label generation.")

