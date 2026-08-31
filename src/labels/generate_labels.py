"""Label generation contracts."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from numbers import Real


class InvalidLabelPriceError(ValueError):
    """Raised when a close price cannot safely be used to generate a label."""


@dataclass(frozen=True)
class GeneratedLabel:
    """Initial binary label based on the first regular session after publication."""

    previous_confirmed_close_date: str
    first_regular_session_date: str
    previous_close: float
    first_session_close: float
    label: str


def classify_up_not_up(previous_close: float, first_session_close: float) -> str:
    """Return the initial MVP label after validating both close prices."""
    validated_previous_close = _validate_label_price("previous_close", previous_close)
    validated_first_session_close = _validate_label_price(
        "first_session_close", first_session_close
    )
    return "up" if validated_first_session_close > validated_previous_close else "not_up"


def _validate_label_price(field_name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise InvalidLabelPriceError(f"{field_name} must be a real numeric value")

    normalized_value = float(value)
    if not isfinite(normalized_value) or normalized_value <= 0:
        raise InvalidLabelPriceError(f"{field_name} must be a finite positive price")

    return normalized_value
