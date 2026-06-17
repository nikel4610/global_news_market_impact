from labels.generate_labels import classify_up_not_up


def test_classify_up_when_first_session_close_is_higher() -> None:
    assert classify_up_not_up(previous_close=100.0, first_session_close=101.0) == "up"


def test_classify_not_up_when_first_session_close_is_equal_or_lower() -> None:
    assert classify_up_not_up(previous_close=100.0, first_session_close=100.0) == "not_up"
    assert classify_up_not_up(previous_close=100.0, first_session_close=99.0) == "not_up"
