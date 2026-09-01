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
) -> PricePair:
    return PricePair(
        ticker=ticker,
        previous=PriceObservation(
            trading_date="2025-06-17",
            close=previous_adjusted_close,
            adjusted_close=previous_adjusted_close,
        ),
        first_session=PriceObservation(
            trading_date="2025-06-18",
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
