# VN30 Momentum Strategy

A systematic momentum strategy backtested on the Vietnamese VN30 index 
from 2018 to 2024, implemented in Python with point-in-time constituent 
data to avoid survivorship bias.

## Overview

This project tests whether momentum — the tendency of recent winners to 
continue outperforming — is priced in Vietnamese large-cap equities. We 
implement and compare multiple momentum strategies using the Jegadeesh & 
Titman (1993) overlapping portfolio framework, adapted for the specific 
characteristics of the Vietnamese market.

## Key Findings

- **Short-horizon momentum dominates**: The 3-1-6 strategy (3-month 
  formation, 1-month skip, 6-month holding) achieves a Sharpe ratio of 
  0.69 for long-short and 0.541 for long-only — significantly outperforming 
  the 12-1-6 specification used in the original JT paper. This suggests 
  Vietnamese retail investor momentum-chasing operates on a shorter horizon 
  than US markets.

- **Long-only beats the benchmark**: The LO 3-1-6 strategy earns 13.88% 
  annualised return vs 8.33% for the equal-weighted VN30 benchmark — a 
  5.5% annual alpha with Sharpe ratio 0.541 vs 0.358.

- **Long-short offers tail risk protection**: Despite lower absolute 
  returns, the LS 3-1-6 strategy limits worst monthly loss to -12.36% 
  vs -29.81% for long-only — useful for risk-constrained investors.

- **JT overlapping smooths returns**: Holding 6 overlapping portfolios 
  simultaneously reduces noise and improves Sharpe ratios versus simple 
  monthly rebalancing across all formation periods.

## Strategy Summary

| Strategy | Ann. Return | Sharpe | Max DD | Worst Month |
|---|---|---|---|---|
| LS 3-1-6 | 10.52% | 0.690 | -23.87% | -12.36% |
| LO 3-1-6 | 13.88% | 0.541 | -42.04% | -29.81% |
| LS 6-1-6 | 9.15% | 0.562 | -35.02% | -11.20% |
| LO 6-1-6 | 12.53% | 0.495 | -44.13% | -29.84% |
| LS 12-1-6 | 6.06% | 0.331 | -45.32% | -9.33% |
| LO 12-1-6 | 11.37% | 0.436 | -44.11% | -28.41% |
| Benchmark | 8.33% | 0.358 | -43.68% | -26.44% |

## Methodology

### Universe
Point-in-time VN30 constituents sourced from official HOSE announcements 
(January and July rebalancing). All 14 rebalancing periods from 2018 to 
2024 verified against official documents. Reserve stocks used to replace 
suspended constituents mid-period.

### Signal
Cross-sectional momentum computed as the compounded return over the 
formation period, skipping the most recent month to avoid short-term 
reversal (Jegadeesh & Titman 1993).

### Portfolio Construction
Stocks ranked into terciles each month using point-in-time VN30 
constituents. Long top tercile (~10 stocks), short bottom tercile 
(~10 stocks), equal-weighted within each group.

**Two implementations:**
- **Monthly rebalancing**: Signal recomputed and portfolio replaced 
  each month
- **JT overlapping**: New portfolio formed each month, held for H months. 
  Monthly return = average across all H simultaneously held portfolios. 
  Reduces noise from any single month's signal.

### Vietnamese Market Adaptations
- **No short selling**: Long-short results are theoretical. Long-only 
  is the practically implementable strategy for most Vietnamese investors.
- **Short horizon**: 3-month formation outperforms 12-month — consistent 
  with retail-dominated market where momentum chasing occurs on shorter 
  cycles.
- **Price limits**: Vietnam's ±7% daily price limit slows information 
  diffusion, potentially extending momentum persistence.

## Project Structure