# TradeAgentLab Report: example

## Summary (strategy)
- CAGR: **22.41%**
- Vol (ann.): **23.43%**
- Sharpe: **0.98**
- Max Drawdown: **-35.97%**
- Beta vs SPY: **0.66**
- Alpha (ann., naive): **12.37%**

- Benchmark (SPY) CAGR: **15.01%**, Sharpe: **0.78**, MDD: **-33.72%**


## Equity (vs benchmark)
![](figures/example_equity_vs_spy.png)

## Drawdown
![](figures/example_drawdown.png)

## Turnover & transaction costs
![](figures/example_turnover_cost.png)

## Latest holdings (top 10 weights)
| Ticker   |   weight |
|:---------|---------:|
| MSFT     |     0.25 |
| NVDA     |     0.25 |
| QQQ      |     0.25 |
| SPY      |     0.25 |

## Monthly returns (%)
|   year |        Jan |      Feb |        Mar |       Apr |       May |       Jun |      Jul |      Aug |       Sep |       Oct |      Nov |        Dec |
|-------:|-----------:|---------:|-----------:|----------:|----------:|----------:|---------:|---------:|----------:|----------:|---------:|-----------:|
|   2020 |  -0.02     |  1.61441 | -11.2586   |  7.79923  |  8.45632  |   8.10107 |  9.63452 | 14.4686  | -3.17049  |  1.90562  |  5.6624  |   3.99393  |
|   2021 |  -0.523009 |  1.08911 |  -3.54188  |  7.71384  | -1.9956   |  11.1136  |  1.52189 |  5.26899 | -4.53508  |  6.91861  |  7.62238 |   0.150043 |
|   2022 |  -7.65936  | -8.37262 |  -0.778714 | -8.35491  | -0.689889 | -10.4937  | 10.5803  | -5.81113 |  0        |  4.7891   | 16.9886  | -11.3721   |
|   2023 |   5.50252  |  4.47567 |  16.8953   |  0.325963 | 11.5291   |   7.61085 |  2.67562 | -5.3815  | -7.98781  | -4.84252  |  9.93664 |   1.33201  |
|   2024 |   7.20803  |  8.84587 |   5.09524  | -7.74062  | 12.2129   |   8.1519  | -1.66256 |  2.91972 | -0.739804 | -0.519376 |  2.69325 |   1.1199   |
|   2025 | -14.8347   | -2.43037 | -12.0222   | -3.74024  | 13.7163   |   8.06758 |  5.13418 |  1.58858 |  4.98224  |  4.50055  | -1.52908 |  -0.137755 |

## Notes
- Costs are modeled as: `turnover * transaction_cost_bps` (simplified).
- This is a research backtest, not investment advice.
