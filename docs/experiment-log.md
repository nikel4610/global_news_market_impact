# Experiment Log

No experiments have been run yet.

Schema contracts, market-session selection, price-row validation, fixture-based article and QQQ/SPY
price selection, adjusted-close label generation, structured exclusions, and leakage-safe feature
group tests are complete. One-session stock, QQQ, and SPY returns and both benchmark-relative excess
returns are also covered by fixture tests and remain excluded from model features.

Before the first experiment, validate data providers and timestamp availability, connect real price
rows to the tested fixture pipeline, implement runtime normalization and leakage-safe joins, and build
the batch label dataset with exclusion summaries. Model training should begin only after those checks
pass.
