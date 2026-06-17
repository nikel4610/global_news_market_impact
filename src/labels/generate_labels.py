"""Label generation contracts."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GeneratedLabel:
    """Initial binary label based on the first regular session after publication."""

    previous_confirmed_close_date: str
    first_regular_session_date: str
    previous_close: float
    first_session_close: float
    label: str


def classify_up_not_up(previous_close: float, first_session_close: float) -> str:
    """Return the initial MVP label."""
    return "up" if first_session_close > previous_close else "not_up"

