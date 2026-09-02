import pytest

from global_news_market_impact.evaluation.returns import (
    ReturnCalculationError,
    calculate_return_metrics,
    calculate_simple_return,
)
from global_news_market_impact.labels.price_rows import PriceObservation, PricePair
from global_news_market_impact.labels.price_validation import InvalidLabelPriceError


def make_price_pair(
    ticker: str,
    previous_adjusted_close: float,
    first_adjusted_close: float,
    *,
    previous_date: str = "2025-06-17",
    first_date: str = "2025-06-18",
) -> PricePair:
    return PricePair(
        ticker=ticker,
        previous=PriceObservation(
            trading_date=previous_date,
            close=previous_adjusted_close,
            adjusted_close=previous_adjusted_close,
        ),
        first_session=PriceObservation(
            trading_date=first_date,
            close=first_adjusted_close,
            adjusted_close=first_adjusted_close,
        ),
    )


def test_simple_return_uses_adjusted_close_ratio() -> None:
    price_pair = make_price_pair("NVDA", 100.0, 110.0)

    assert calculate_simple_return(price_pair) == pytest.approx(0.1)


def test_return_metrics_calculate_both_excess_returns() -> None:
    metrics = calculate_return_metrics(
        stock_price_pair=make_price_pair("NVDA", 100.0, 110.0),
        benchmark_price_pairs=(
            make_price_pair("QQQ", 100.0, 105.0),
            make_price_pair("SPY", 200.0, 202.0),
        ),
    )

    assert metrics.stock_return == pytest.approx(0.1)
    assert metrics.qqq_return == pytest.approx(0.05)
    assert metrics.spy_return == pytest.approx(0.01)
    assert metrics.excess_return_vs_qqq == pytest.approx(0.05)
    assert metrics.excess_return_vs_spy == pytest.approx(0.09)


def test_return_metrics_match_benchmarks_by_ticker_not_tuple_order() -> None:
    metrics = calculate_return_metrics(
        stock_price_pair=make_price_pair("NVDA", 100.0, 102.0),
        benchmark_price_pairs=(
            make_price_pair("SPY", 100.0, 101.0),
            make_price_pair("QQQ", 100.0, 103.0),
        ),
    )

    assert metrics.qqq_return == pytest.approx(0.03)
    assert metrics.spy_return == pytest.approx(0.01)
    assert metrics.excess_return_vs_qqq == pytest.approx(-0.01)
    assert metrics.excess_return_vs_spy == pytest.approx(0.01)


def test_equal_adjusted_closes_produce_zero_return() -> None:
    assert calculate_simple_return(make_price_pair("NVDA", 100.0, 100.0)) == 0.0


@pytest.mark.parametrize("invalid_previous", [0.0, float("nan")])
def test_simple_return_rejects_invalid_previous_adjusted_close(
    invalid_previous: float,
) -> None:
    with pytest.raises(InvalidLabelPriceError):
        calculate_simple_return(make_price_pair("NVDA", invalid_previous, 101.0))


def test_return_metrics_reject_missing_benchmark() -> None:
    with pytest.raises(ReturnCalculationError, match="missing benchmark price pairs: SPY"):
        calculate_return_metrics(
            stock_price_pair=make_price_pair("NVDA", 100.0, 101.0),
            benchmark_price_pairs=(make_price_pair("QQQ", 100.0, 101.0),),
        )


def test_return_metrics_reject_duplicate_benchmark() -> None:
    with pytest.raises(ReturnCalculationError, match="duplicate benchmark price pair: QQQ"):
        calculate_return_metrics(
            stock_price_pair=make_price_pair("NVDA", 100.0, 101.0),
            benchmark_price_pairs=(
                make_price_pair("QQQ", 100.0, 101.0),
                make_price_pair("QQQ", 100.0, 102.0),
                make_price_pair("SPY", 100.0, 101.0),
            ),
        )


@pytest.mark.parametrize(
    ("benchmark_ticker", "session_name", "previous_date", "first_date"),
    [
        ("QQQ", "previous", "2025-06-16", "2025-06-18"),
        ("QQQ", "first_session", "2025-06-17", "2025-06-19"),
        ("SPY", "previous", "2025-06-16", "2025-06-18"),
        ("SPY", "first_session", "2025-06-17", "2025-06-19"),
    ],
)
def test_return_metrics_reject_misaligned_benchmark_dates(
    benchmark_ticker: str,
    session_name: str,
    previous_date: str,
    first_date: str,
) -> None:
    benchmark_pairs = {
        "QQQ": make_price_pair("QQQ", 100.0, 101.0),
        "SPY": make_price_pair("SPY", 100.0, 101.0),
    }
    benchmark_pairs[benchmark_ticker] = make_price_pair(
        benchmark_ticker,
        100.0,
        101.0,
        previous_date=previous_date,
        first_date=first_date,
    )

    with pytest.raises(
        ReturnCalculationError,
        match=(
            rf"{benchmark_ticker} {session_name} trading date mismatch: "
            rf"expected 2025-06-(17|18), got 2025-06-(16|19)"
        ),
    ):
        calculate_return_metrics(
            stock_price_pair=make_price_pair("NVDA", 100.0, 101.0),
            benchmark_price_pairs=tuple(benchmark_pairs.values()),
        )
