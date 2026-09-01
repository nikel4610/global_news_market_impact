from global_news_market_impact.config.tickers import (
    MARKET_BENCHMARK_NAMES,
    MARKET_BENCHMARK_TICKERS,
    MVP_TICKERS,
)


def test_market_benchmarks_are_not_prediction_tickers() -> None:
    assert MARKET_BENCHMARK_TICKERS == ("QQQ", "SPY")
    assert set(MARKET_BENCHMARK_TICKERS).isdisjoint(MVP_TICKERS)


def test_market_benchmarks_have_explicit_index_names() -> None:
    assert MARKET_BENCHMARK_NAMES == {
        "QQQ": "Nasdaq-100",
        "SPY": "S&P 500",
    }
