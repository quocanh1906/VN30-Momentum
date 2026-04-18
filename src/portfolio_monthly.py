import pandas as pd
import numpy as np
from data import VN30_CONSTITUENTS, VN30_RESERVES
from signals import VN30_REBALANCE_DATES, build_rebalance_schedule

def build_portfolios(prices, momentum):
    """
    Construct long-only and long-short momentum portfolios
    with MONTHLY rebalancing.

    Each month:
    - Use point-in-time VN30 constituents active that month
    - Rank by 12-1 momentum signal into terciles
    - Long top tercile, short bottom tercile (equal weighted)
    - Long only: buy top tercile, hold cash for rest

    Parameters
    ----------
    prices   : DataFrame, monthly prices
    momentum : DataFrame, momentum signals from compute_momentum()
    """
    monthly_returns = prices.pct_change()
    results         = []
    periods         = sorted(VN30_CONSTITUENTS.keys())

    for date in momentum.index:

        # Skip if no momentum signal yet (first 12 months)
        if momentum.loc[date].isna().all():
            continue

        # Get point-in-time VN30 constituents for this month
        year  = date.year
        month = date.month
        key   = f"{year}-01" if month < 7 else f"{year}-07"

        # Fall back to most recent available period
        if key not in VN30_CONSTITUENTS:
            available = [p for p in periods if p <= key]
            if not available:
                continue
            key = available[-1]

        constituents = VN30_CONSTITUENTS[key]
        reserves     = VN30_RESERVES.get(key, [])

        # Get momentum scores for active constituents only
        scores = momentum.loc[date,
                              [t for t in constituents
                               if t in momentum.columns]]
        scores = scores.dropna()

        if len(scores) < 6:
            continue

        # Rank into terciles
        try:
            tercile_labels = pd.qcut(scores, q=3,
                                     labels=["bottom","mid","top"])
        except ValueError:
            continue

        top    = tercile_labels[tercile_labels == "top"].index.tolist()
        bottom = tercile_labels[tercile_labels == "bottom"].index.tolist()

        # Get next month returns (trade at end of month t, earn month t+1)
        loc = monthly_returns.index.get_loc(date)
        if loc + 1 >= len(monthly_returns):
            continue
        next_date    = monthly_returns.index[loc + 1]
        next_returns = monthly_returns.iloc[loc + 1]

        # Handle suspended stocks — replace with reserves
        active_top    = []
        active_bottom = []

        for ticker in top:
            if ticker in next_returns.index and pd.notna(next_returns[ticker]):
                active_top.append(ticker)
            else:
                for reserve in reserves:
                    if (reserve not in top + bottom and
                        reserve in next_returns.index and
                        pd.notna(next_returns[reserve])):
                        active_top.append(reserve)
                        break

        for ticker in bottom:
            if ticker in next_returns.index and pd.notna(next_returns[ticker]):
                active_bottom.append(ticker)
            else:
                for reserve in reserves:
                    if (reserve not in top + bottom + active_top and
                        reserve in next_returns.index and
                        pd.notna(next_returns[reserve])):
                        active_bottom.append(reserve)
                        break

        # Compute equal-weighted returns
        top_ret = next_returns[active_top].mean() if active_top else np.nan
        bot_ret = next_returns[active_bottom].mean() if active_bottom else np.nan

        ls_ret = top_ret - bot_ret if pd.notna(top_ret) and pd.notna(bot_ret) else np.nan
        lo_ret = top_ret if pd.notna(top_ret) else np.nan

        results.append({
            "date"             : next_date,
            "long_short_return": ls_ret,
            "long_only_return" : lo_ret,
            "top_stocks"       : active_top,
            "bottom_stocks"    : active_bottom,
            "n_top"            : len(active_top),
            "n_bottom"         : len(active_bottom),
        })

    return pd.DataFrame(results).set_index("date")

def compute_benchmark(prices, index_ticker=None):
    """
    Compute equal-weighted VN30 benchmark return each month.
    Uses point-in-time constituents — only stocks actually in VN30
    at each point are included in the benchmark.
    """
    monthly_returns = prices.pct_change()
    benchmark       = []

    periods = sorted(VN30_CONSTITUENTS.keys())

    for i, period in enumerate(periods):
        constituents = VN30_CONSTITUENTS[period]

        # Active window for this period
        year, month = period.split("-")
        start = pd.Timestamp(f"{year}-{month}-01")
        end   = (
            pd.Timestamp(f"{periods[i+1].split('-')[0]}-"
                         f"{periods[i+1].split('-')[1]}-01")
            if i + 1 < len(periods)
            else pd.Timestamp("2025-01-31")
        )

        dates = monthly_returns.index[
            (monthly_returns.index >= start) &
            (monthly_returns.index < end)
        ]

        for date in dates:
            valid = [t for t in constituents
                     if t in monthly_returns.columns
                     and pd.notna(monthly_returns.loc[date, t])]
            if valid:
                benchmark.append({
                    "date"  : date,
                    "return": monthly_returns.loc[date, valid].mean()
                })

    bm = pd.DataFrame(benchmark).set_index("date")["return"]
    bm.name = "benchmark"
    return bm

if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")

    prices = pd.read_csv(
        "data/processed/prices.csv",
        index_col=0, parse_dates=True
    )
    print(f"Loaded prices: {prices.shape}")

    from signals import compute_momentum
    momentum = compute_momentum(prices)

    print("\nBuilding portfolios (monthly rebalancing)...")
    portfolios = build_portfolios(prices, momentum)
    benchmark  = compute_benchmark(prices)
    benchmark  = benchmark.reindex(portfolios.index)

    print(f"\nPortfolio period: {portfolios.index[0].date()} "
          f"to {portfolios.index[-1].date()}")
    print(f"Months          : {len(portfolios)}")

    print("\nSample output (last 6 months):")
    print(portfolios[["long_short_return","long_only_return",
                       "n_top","n_bottom"]].tail(6).round(4))

    import os
    os.makedirs("data/processed", exist_ok=True)
    portfolios.to_csv("data/processed/portfolios.csv")
    benchmark.to_csv("data/processed/benchmark.csv")
    print("\nSaved to data/processed/")