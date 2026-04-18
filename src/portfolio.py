import pandas as pd
import numpy as np
from data import VN30_CONSTITUENTS, VN30_RESERVES
from signals import VN30_REBALANCE_DATES, build_rebalance_schedule

def build_portfolios(prices, schedule):
    """
    Construct long-only and long-short momentum portfolios
    based on VN30 rebalancing schedule.

    Rules:
    - Rebalance every January and July (matching VN30 schedule)
    - Long top tercile, short bottom tercile (equal weighted)
    - Long only: buy top tercile, hold cash for rest
    - Hold from rebalance date until next rebalance date
    - If stock suspended mid-period: replace with first available reserve

    Parameters
    ----------
    prices   : DataFrame, monthly prices
    schedule : list of dicts from build_rebalance_schedule()

    Returns
    -------
    results : DataFrame with columns:
        date, long_short_return, long_only_return,
        top_portfolio, bottom_portfolio, period
    """
    monthly_returns = prices.pct_change()
    results = []

    for i, rebal in enumerate(schedule):
        period        = rebal["period"]
        rebal_date    = rebal["rebalance_date"]
        top           = rebal["top"]
        bottom        = rebal["bottom"]
        reserves      = rebal["reserves"]

        # Define holding period: from this rebalance to next
        if i + 1 < len(schedule):
            next_rebal_date = schedule[i + 1]["rebalance_date"]
        else:
            next_rebal_date = pd.Timestamp("2025-01-31")

        # Get monthly dates in holding period
        holding_dates = monthly_returns.index[
            (monthly_returns.index > rebal_date) &
            (monthly_returns.index <= next_rebal_date)
        ]

        if len(holding_dates) == 0:
            continue

        # For each month in holding period, compute portfolio return
        for date in holding_dates:

            # Check for suspended stocks and replace with reserves
            active_top    = []
            active_bottom = []

            for ticker in top:
                if ticker in monthly_returns.columns:
                    ret = monthly_returns.loc[date, ticker]
                    if pd.notna(ret):
                        active_top.append(ticker)
                    else:
                        # Try to replace with first available reserve
                        for reserve in reserves:
                            if reserve not in top + bottom:
                                if reserve in monthly_returns.columns:
                                    if pd.notna(monthly_returns.loc[date, reserve]):
                                        active_top.append(reserve)
                                        break

            for ticker in bottom:
                if ticker in monthly_returns.columns:
                    ret = monthly_returns.loc[date, ticker]
                    if pd.notna(ret):
                        active_bottom.append(ticker)
                    else:
                        for reserve in reserves:
                            if reserve not in top + bottom + active_top:
                                if reserve in monthly_returns.columns:
                                    if pd.notna(monthly_returns.loc[date, reserve]):
                                        active_bottom.append(reserve)
                                        break

            # Compute equal-weighted returns
            if len(active_top) > 0:
                top_ret = monthly_returns.loc[date, active_top].mean()
            else:
                top_ret = np.nan

            if len(active_bottom) > 0:
                bot_ret = monthly_returns.loc[date, active_bottom].mean()
            else:
                bot_ret = np.nan

            # Long-short: top minus bottom
            if pd.notna(top_ret) and pd.notna(bot_ret):
                ls_ret = top_ret - bot_ret
            else:
                ls_ret = np.nan

            # Long-only: top tercile only (cash = 0% for rest)
            lo_ret = top_ret if pd.notna(top_ret) else np.nan

            results.append({
                "date"             : date,
                "period"           : period,
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

    # Load prices
    prices = pd.read_csv(
        "data/processed/prices.csv",
        index_col=0,
        parse_dates=True
    )
    print(f"Loaded prices: {prices.shape}")

    # Build signal schedule
    from signals import build_rebalance_schedule
    momentum, schedule = build_rebalance_schedule(prices)

    # Build portfolios
    print("\nBuilding portfolios...")
    portfolios = build_portfolios(prices, schedule)
    benchmark  = compute_benchmark(prices)

    # Align benchmark to portfolio period
    benchmark = benchmark.reindex(portfolios.index)

    print(f"\nPortfolio period: {portfolios.index[0].date()} "
          f"to {portfolios.index[-1].date()}")
    print(f"Months          : {len(portfolios)}")

    print("\nSample output (last 6 months):")
    print(portfolios[["long_short_return","long_only_return",
                       "n_top","n_bottom"]].tail(6).round(4))

    print("\nBenchmark (last 6 months):")
    print(benchmark.tail(6).round(4))

    # Save
    import os
    os.makedirs("data/processed", exist_ok=True)
    portfolios.to_csv("data/processed/portfolios.csv")
    benchmark.to_csv("data/processed/benchmark.csv")
    print("\nSaved to data/processed/")