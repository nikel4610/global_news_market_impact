import pandas as pd
import pytest

from labels.generate_labels import InvalidLabelPriceError, classify_up_not_up

INVALID_PRICES = [
    pytest.param(None, id="none"),
    pytest.param("100.0", id="string"),
    pytest.param(True, id="bool"),
    pytest.param(float("nan"), id="nan"),
    pytest.param(float("inf"), id="positive-infinity"),
    pytest.param(float("-inf"), id="negative-infinity"),
    pytest.param(0.0, id="zero"),
    pytest.param(-1.0, id="negative"),
]


def test_classify_up_when_first_session_close_is_higher() -> None:
    assert classify_up_not_up(previous_close=100.0, first_session_close=101.0) == "up"


def test_classify_not_up_when_first_session_close_is_equal() -> None:
    assert classify_up_not_up(previous_close=100.0, first_session_close=100.0) == "not_up"


def test_classify_not_up_when_first_session_close_is_lower() -> None:
    assert classify_up_not_up(previous_close=100.0, first_session_close=99.0) == "not_up"


def test_classify_accepts_pandas_numpy_real_scalars() -> None:
    prices = pd.Series([100.0, 101.0], dtype="float32")

    assert (
        classify_up_not_up(previous_close=prices.iloc[0], first_session_close=prices.iloc[1])
        == "up"
    )


@pytest.mark.parametrize("invalid_price", INVALID_PRICES)
def test_invalid_previous_close_is_rejected_with_field_name(invalid_price: object) -> None:
    with pytest.raises(InvalidLabelPriceError, match="previous_close"):
        classify_up_not_up(previous_close=invalid_price, first_session_close=101.0)  # type: ignore[arg-type]


@pytest.mark.parametrize("invalid_price", INVALID_PRICES)
def test_invalid_first_session_close_is_rejected_with_field_name(invalid_price: object) -> None:
    with pytest.raises(InvalidLabelPriceError, match="first_session_close"):
        classify_up_not_up(previous_close=100.0, first_session_close=invalid_price)  # type: ignore[arg-type]
