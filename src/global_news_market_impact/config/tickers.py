"""MVP ticker universe."""

MVP_TICKERS: tuple[str, ...] = (
    "NVDA",
    "AVGO",
    "AMD",
    "MU",
    "AAPL",
    "MSFT",
    "GOOGL",
    "TSLA",
)

MARKET_BENCHMARK_TICKERS: tuple[str, ...] = (
    "QQQ",
    "SPY",
)

MARKET_BENCHMARK_NAMES: dict[str, str] = {
    "QQQ": "Nasdaq-100",
    "SPY": "S&P 500",
}
