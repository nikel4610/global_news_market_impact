"""Shared validation for raw and adjusted close prices."""

from __future__ import annotations

from math import isfinite
from numbers import Real


class InvalidLabelPriceError(ValueError):
    """Raised when a price cannot safely be used for a label row."""


def validate_positive_price(field_name: str, value: object) -> float:
    """Return a normalized positive finite price or raise an explicit error."""
    if isinstance(value, bool) or not isinstance(value, Real):
        raise InvalidLabelPriceError(f"{field_name} must be a real numeric value")

    normalized_value = float(value)
    if not isfinite(normalized_value) or normalized_value <= 0:
        raise InvalidLabelPriceError(f"{field_name} must be a finite positive price")

    return normalized_value
