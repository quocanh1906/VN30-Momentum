# VN30 Momentum Strategy

A systematic momentum study on the Vietnamese VN30 equity index using the Jegadeesh-Titman (1993) overlapping portfolio methodology. The project tests whether cross-sectional momentum generates risk-adjusted excess returns in the Vietnamese market and examines how formation period length and transaction costs affect strategy viability.

---

## Key Findings

### 1. Long-only momentum beats the benchmark
The 3-month formation long-only strategy (LO 3-1-6) delivers **16.29% annualised return** with a Sharpe of **0.698**, outperforming the E1VFVN30 ETF benchmark (12.97% return, Sharpe 0.645). The 3-month formation consistently outperforms the 12-month formation, suggesting Vietnamese market momentum operates on a shorter horizon than the US market.

### 2. Short formation outperforms long formation
| Strategy   | Ann. Return (%) | Sharpe | Max Drawdown (%) |
|------------|----------------|--------|-----------------|
| LO 3-1-6   | 16.29          | 0.698  | -43.19          |
| LO 12-1-6  | 16.68          | 0.671  | -47.46          |
| LS 3-1-6   | 4.12           | 0.298  | -23.51          |
| LS 12-1-6  | 2.04           | 0.110  | -47.69          |
| Benchmark  | 12.97          | 0.645  | -43.06          |

The 3-month formation generates comparable returns to the 12-month with lower drawdown, consistent with a retail-dominated market where momentum chasing occurs on shorter cycles. The +/-7% daily price limit on HOSE may also slow information diffusion, extending short-term momentum persistence.

### 3. Long-short strategy generates modest alpha
The long-short strategy (LS 3-1-6) delivers 4.12% annualised with a Sharpe of 0.298 before costs. This modest spread reflects the absence of short selling in practice — the long-short results are theoretical and assume costless shorting, which is not available to most Vietnamese market participants.

### 4. Transaction costs are manageable at monthly frequency
| Scenario     | One-way Cost | Round-trip | Ann. Return (%) | Sharpe |
|--------------|-------------|-----------|----------------|--------|
| No cost      | 0.000%      | 0.000%    | 4.12           | 0.298  |
| Realistic    | 0.125%      | 0.250%    | 3.10           | 0.224  |
| Conservative | 0.175%      | 0.350%    | 2.70           | 0.195  |

Monthly rebalancing with 6-month holding significantly reduces cost drag compared to weekly strategies. The long-short strategy retains positive alpha even under conservative cost assumptions.

### 5. Momentum is regime-dependent
The rolling 12-month Sharpe analysis shows momentum alpha is not stable across time:
- **2016-2017**: Positive but volatile (early strategy period)
- **2020**: Sharp spike to Sharpe ~2.8 (COVID momentum worked strongly)
- **2022-2023**: Deep drawdown, Sharpe turns sharply negative (momentum crash during VN market sell-off)
- **2024**: Recovery, Sharpe returning above 1.0

LS 3-1-6 has positive rolling Sharpe in **62.5% of months** — decent but not consistent enough to deploy without regime filters.

---

## Methodology

### Universe
Point-in-time VN30 constituents sourced from official HOSE announcements across all 14 rebalancing periods (January 2018 to July 2024). Using point-in-time lists eliminates survivorship bias — stocks that were removed from VN30 (NVL, PDR, ROS, FLC-related stocks) are included during their active periods.

### Signal
Cross-sectional momentum: compounded return over the formation period, skipping the most recent 1 month to avoid short-term reversal (Jegadeesh & Titman, 1993).

At month t: `signal = compounded return from t - formation - 1 to t - 1`

### Portfolio Construction
Jegadeesh-Titman overlapping portfolios:
- Every month, form a new portfolio by ranking VN30 constituents into terciles by momentum
- Hold each portfolio for 6 months
- Monthly return = equal-weighted average across all 6 simultaneously held portfolios
- Long top tercile (~10 stocks), short bottom tercile (~10 stocks)

### Benchmark
**E1VFVN30 ETF** — the actual investable product tracking the VN30 index, downloaded from vnstock (KBS source). This is a more realistic benchmark than an equal-weighted index since it reflects what an investor would actually hold as an alternative.

### Transaction Costs
Applied on portfolio entry (month 1) and exit (month 6) only:
- **Realistic**: 0.125% one-way = 0.25% round-trip
  - 0.1% mandatory sales tax (SSC regulation, sell side only)
  - ~0.10-0.15% brokerage for institutional VN30 orders
- **Conservative**: 0.175% one-way = 0.35% round-trip (adds slippage estimate)

### Suspended Stock Handling
If a constituent is suspended or has missing data in a given month, it is replaced by the highest-ranked reserve stock from the official HOSE reserve list for that period. Reserve lists are sourced from the same HOSE announcements as the constituent lists.

### Cold Start Handling
Stocks that IPO'd after 2015 (HDB, GVR, BCM, POW, TPB, VHM etc.) do not have sufficient history to compute a momentum signal immediately upon entering VN30. These stocks produce NaN momentum scores and are automatically excluded from ranking for that period. The reserve substitution logic fills in if needed. This is the most conservative and academically honest approach.

---

## Data

### Sources
- **Price data**: vnstock (KBS source), daily prices resampled to monthly end-of-month closes
- **ROS**: Manually sourced from cafef.vn (vnstock has no data for ROS following the FLC fraud scandal). First-of-month prices shifted by one month to approximate month-end prices
- **VN30 constituents**: Official HOSE announcements for all 14 rebalancing periods (2018-01 through 2024-07)
- **Reserve lists**: HOSE official reserve announcements
- **Benchmark**: E1VFVN30 ETF via vnstock (KBS source)

### Coverage
- **Universe**: 63 unique tickers (all stocks ever in VN30 or reserve list 2018-2024)
- **Price period**: September 2015 to December 2024 (112 months)
- **Strategy period**: January 2016 to December 2024 (after formation period warmup)
- **All 14 VN30 rebalancing periods**: 100% constituent coverage verified

### Data Quality
All gaps in price history are pre-IPO or post-delisting — there are no genuine mid-history gaps for any ticker. Verified programmatically by checking for NaN values between each ticker's first and last valid observation.

---

## Assumptions and Limitations

### Assumptions made
- Equal weighting within top and bottom terciles
- Positions entered and exited at end-of-month prices (no intraday execution)
- 6 overlapping portfolios held simultaneously at all times
- Reserve substitution is costless and immediate
- ROS price data is shifted by one month to approximate month-end — introduces minor timing mismatch for one stock

### Frictions neglected
- **Market impact**: Large orders in less liquid VN30 stocks would move prices. Not modelled
- **Borrowing costs for short positions**: Short selling is restricted in Vietnam — the long-short results are theoretical only
- **Dividend adjustments**: Prices are not dividend-adjusted, which may slightly overstate or understate returns
- **Foreign ownership limits (FOL)**: Several VN30 stocks are at or near FOL, restricting foreign investor access. Not modelled
- **T+2 settlement**: Vietnamese market uses T+2 settlement, meaning execution at exact month-end prices is an approximation

### Sample limitations
- **Short history**: 107 months (~9 years) is relatively short for robust momentum inference. Standard momentum research uses 20+ years
- **Single market**: Results may not generalise beyond the Vietnamese frontier market context
- **No short selling**: Long-short results assume frictionless shorting unavailable to most participants

---

## Project Structure

```
VN30-Momentum/
├── main.py                  <- run full pipeline
├── src/
│   ├── data.py              <- VN30 constituents, vnstock download, ROS injection
│   ├── signals.py           <- momentum signal computation and ranking
│   ├── portfolio.py         <- JT overlapping portfolios + benchmark
│   └── performance.py       <- metrics, rolling Sharpe, visualisation
├── data/
│   ├── processed/           <- generated by src/data.py (not tracked)
│   └── README.md            <- data sources
└── output/
    ├── performance_comparison.png
    ├── transaction_cost_impact.png
    ├── rolling_sharpe.png
    └── all_strategies.csv
```

---

## How to Run

```bash
# Install dependencies
pip install pandas numpy matplotlib vnstock

# Download price data (~5-6 minutes due to rate limiting)
python src/data.py

# Run full pipeline
python main.py
```

> **Note:** Price data is not included in this repository. Run `python src/data.py` first to download all data before running `main.py`.

---

## References

- Jegadeesh, N. & Titman, S. (1993). *Returns to Buying Winners and Selling Losers: Implications for Stock Market Efficiency.* Journal of Finance, 48(1), 65-91.
- Lesmond, D., Schill, M. & Zhou, C. (2004). *The Illusory Nature of Momentum Profits.* Journal of Financial Economics, 71(2), 349-380.
- State Securities Commission of Vietnam. *Securities Law No. 54/2019/QH14*, effective January 2021.

---

## Author

Vu Quoc Anh Nguyen — MSc Risk Management & Financial Engineering, Imperial College London
GitHub: [quocanh1906](https://github.com/quocanh1906)
