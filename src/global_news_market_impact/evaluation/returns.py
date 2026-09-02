"""One-session returns for the article stock and market benchmarks."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from math import isfinite

from global_news_market_impact.config.tickers import MARKET_BENCHMARK_TICKERS
from global_news_market_impact.labels.price_rows import PricePair
from global_news_market_impact.labels.price_validation import validate_positive_price


class ReturnCalculationError(ValueError):
    """Raised when aligned price pairs cannot produce evaluation returns."""


@dataclass(frozen=True)
class ReturnMetrics:
    stock_return: float
    qqq_return: float
    spy_return: float
    excess_return_vs_qqq: float
    excess_return_vs_spy: float


def calculate_simple_return(price_pair: PricePair) -> float:
    """Calculate one-session simple return from adjusted closes."""
    previous_adjusted_close = validate_positive_price(
        f"{price_pair.ticker}.previous_adjusted_close",
        price_pair.previous.adjusted_close,
    )
    first_session_adjusted_close = validate_positive_price(
        f"{price_pair.ticker}.first_session_adjusted_close",
        price_pair.first_session.adjusted_close,
    )
    simple_return = first_session_adjusted_close / previous_adjusted_close - 1.0
    if not isfinite(simple_return):
        raise ReturnCalculationError(f"non-finite return for {price_pair.ticker}")
    return simple_return


def calculate_return_metrics(
    *,
    stock_price_pair: PricePair,
    benchmark_price_pairs: Iterable[PricePair],
) -> ReturnMetrics:
    """Calculate stock and QQQ/SPY returns without relying on tuple order."""
    benchmark_pairs_by_ticker: dict[str, PricePair] = {}
    for price_pair in benchmark_price_pairs:
        if price_pair.ticker in benchmark_pairs_by_ticker:
            raise ReturnCalculationError(f"duplicate benchmark price pair: {price_pair.ticker}")
        benchmark_pairs_by_ticker[price_pair.ticker] = price_pair

    required_benchmarks = set(MARKET_BENCHMARK_TICKERS)
    actual_benchmarks = set(benchmark_pairs_by_ticker)
    missing_benchmarks = sorted(required_benchmarks - actual_benchmarks)
    unexpected_benchmarks = sorted(actual_benchmarks - required_benchmarks)
    if missing_benchmarks:
        raise ReturnCalculationError(
            f"missing benchmark price pairs: {', '.join(missing_benchmarks)}"
        )
    if unexpected_benchmarks:
        raise ReturnCalculationError(
            f"unexpected benchmark price pairs: {', '.join(unexpected_benchmarks)}"
        )

    _validate_benchmark_dates(
        stock_price_pair=stock_price_pair,
        benchmark_pairs_by_ticker=benchmark_pairs_by_ticker,
    )

    stock_return = calculate_simple_return(stock_price_pair)
    qqq_return = calculate_simple_return(benchmark_pairs_by_ticker["QQQ"])
    spy_return = calculate_simple_return(benchmark_pairs_by_ticker["SPY"])
    return ReturnMetrics(
        stock_return=stock_return,
        qqq_return=qqq_return,
        spy_return=spy_return,
        excess_return_vs_qqq=stock_return - qqq_return,
        excess_return_vs_spy=stock_return - spy_return,
    )


def _validate_benchmark_dates(
    *,
    stock_price_pair: PricePair,
    benchmark_pairs_by_ticker: dict[str, PricePair],
) -> None:
    expected_dates = {
        "previous": stock_price_pair.previous.trading_date,
        "first_session": stock_price_pair.first_session.trading_date,
    }
    for benchmark_ticker in MARKET_BENCHMARK_TICKERS:
        benchmark_pair = benchmark_pairs_by_ticker[benchmark_ticker]
        actual_dates = {
            "previous": benchmark_pair.previous.trading_date,
            "first_session": benchmark_pair.first_session.trading_date,
        }
        for session_name, expected_date in expected_dates.items():
            actual_date = actual_dates[session_name]
            if actual_date != expected_date:
                raise ReturnCalculationError(
                    f"{benchmark_ticker} {session_name} trading date mismatch: "
                    f"expected {expected_date}, got {actual_date}"
                )
