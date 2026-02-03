# TradeAgentLab Report: example

## Summary (strategy)
- CAGR: **13.78%**
- Vol (ann.): **14.20%**
- Sharpe: **0.98**
- Max Drawdown: **-27.39%**
- Beta vs SPY: **0.37**
- Alpha (ann., naive): **7.94%**

- Benchmark (SPY) CAGR: **15.01%**, Sharpe: **0.78**, MDD: **-33.72%**


## Equity (vs benchmark)
![](figures/example_equity_vs_spy.png)

## Drawdown
![](figures/example_drawdown.png)

## Turnover & transaction costs
![](figures/example_turnover_cost.png)

## Risk overlay (exposure scale)
- Last scale: **1.00**
- Days killed (scale=0 due to DD): **0**

![](figures/example_risk_scale.png)

## Latest holdings (top 10 weights)
| Ticker   |   weight |
|:---------|---------:|
| MSFT     |     0.25 |
| NVDA     |     0.25 |
| QQQ      |     0.25 |
| SPY      |     0.25 |

## Monthly returns (%)
|   year |       Jan |       Feb |       Mar |       Apr |       May |       Jun |       Jul |      Aug |       Sep |       Oct |      Nov |       Dec |
|-------:|----------:|----------:|----------:|----------:|----------:|----------:|----------:|---------:|----------:|----------:|---------:|----------:|
|   2020 | -0.02     |  3.83298  | -2.38731  |  5.5305   |  3.38168  |   3.4819  |  4.04824  |  7.24987 | -2.25005  | -0.798122 |  2.85227 |  3.07583  |
|   2021 | -0.663275 |  0.136467 | -1.56749  |  7.0759   | -0.601034 |   6.46931 |  1.21458  |  5.01488 | -3.38765  |  6.74025  |  6.65179 |  0.287863 |
|   2022 | -3.82271  | -8.31136  | -0.270962 | -4.63518  | -0.689889 | -10.4203  |  6.12802  | -2.71825 |  0        |  4.27329  |  5.59442 | -3.82257  |
|   2023 |  2.62598  |  2.59456  |  5.93404  |  0.461361 |  7.20087  |   4.01383 |  2.04335  | -4.45606 | -4.29241  | -4.17769  |  4.9222  |  1.0688   |
|   2024 |  5.20851  |  6.06599  |  2.21093  | -6.27833  |  7.87639  |   6.39848 | -0.980421 |  2.23027 | -0.839927 | -0.150648 |  1.94249 |  0.16029  |
|   2025 | -8.33365  | -2.8667   | -6.03715  | -3.87577  |  7.58619  |   6.05228 |  5.10741  |  1.50897 |  4.88878  |  2.62679  | -1.05416 |  0.215474 |

## Notes
- Costs are modeled as: `turnover * transaction_cost_bps` (simplified).
- This is a research backtest, not investment advice.
