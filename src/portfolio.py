import pandas as pd
import numpy as np
from data import VN30_CONSTITUENTS, VN30_RESERVES
from signals import compute_momentum, rank_signals


def build_portfolios(prices, formation=3, skip=1, holding=6,
                     cost_per_trade=0.0):
    """
    Jegadeesh-Titman (1993) overlapping momentum portfolios at monthly frequency.

    Every month t:
    - Form a new portfolio based on past 'formation' months of returns,
      skipping the most recent 'skip' month
    - Hold each portfolio for 'holding' months
    - Monthly return = equal-weighted average across all overlapping
      portfolios currently being held

    Cold start handling:
    - Stocks with fewer than formation+skip months of history have NaN
      momentum scores and are excluded from ranking automatically
    - If excluded stock is a constituent, reserve substitution applies
    - If universe drops below 6 rankable stocks, that month is skipped

    Transaction costs (realistic Vietnamese market, 2024):
    - Sales tax: 0.1% on sell side (mandatory, SSC regulation)
    - Brokerage: 0.10-0.15% for institutional VN30 orders
    - Optimistic  : 0.075% one-way = 0.15% round-trip
    - Realistic   : 0.125% one-way = 0.25% round-trip
    - Conservative: 0.175% one-way = 0.35% round-trip

    Parameters
    ----------
    prices        : DataFrame, monthly end-of-month prices
    formation     : int, momentum lookback in months (default 3)
    skip          : int, months to skip (default 1)
    holding       : int, holding period in months (default 6)
    cost_per_trade: float, one-way cost as fraction (default 0)

    Returns
    -------
    DataFrame with columns: long_short_return, long_only_return, n_portfolios
    """
    monthly_returns = prices.pct_change()
    momentum        = compute_momentum(prices, lookback=formation, skip=skip)
    portfolio_plans = {}

    # Step 1: form a portfolio every month, plan it H months ahead
    for i, signal_date in enumerate(momentum.index):

        row = momentum.loc[signal_date]
        if row.isna().all():
            continue

        ranking = rank_signals(momentum, signal_date)
        if ranking is None:
            continue

        top      = ranking["top"]
        bottom   = ranking["bottom"]
        reserves = ranking["reserves"]

        for h in range(1, holding + 1):
            future_idx = i + h
            if future_idx >= len(monthly_returns.index):
                break

            future_date = monthly_returns.index[future_idx]

            if future_date not in portfolio_plans:
                portfolio_plans[future_date] = []

            portfolio_plans[future_date].append({
                "top"     : top,
                "bottom"  : bottom,
                "reserves": reserves,
                "entry"   : h == 1,
                "exit"    : h == holding,
            })

    # Step 2: each month average returns across all active portfolios
    results = []

    for date in monthly_returns.index:
        if date not in portfolio_plans:
            continue

        active   = portfolio_plans[date]
        next_ret = monthly_returns.loc[date]

        ls_returns = []
        lo_returns = []

        for plan in active:
            top      = plan["top"]
            bottom   = plan["bottom"]
            reserves = plan["reserves"]

            # Handle suspended or missing stocks — replace with reserves
            active_top    = []
            active_bottom = []

            for ticker in top:
                if ticker in next_ret.index and pd.notna(next_ret[ticker]):
                    active_top.append(ticker)
                else:
                    for r in reserves:
                        if (r not in top + bottom and
                            r in next_ret.index and
                            pd.notna(next_ret[r])):
                            active_top.append(r)
                            break

            for ticker in bottom:
                if ticker in next_ret.index and pd.notna(next_ret[ticker]):
                    active_bottom.append(ticker)
                else:
                    for r in reserves:
                        if (r not in top + bottom + active_top and
                            r in next_ret.index and
                            pd.notna(next_ret[r])):
                            active_bottom.append(r)
                            break

            top_ret = next_ret[active_top].mean() if active_top else np.nan
            bot_ret = next_ret[active_bottom].mean() if active_bottom else np.nan

            # Apply transaction costs on entry and exit only
            tc = 0.0
            if cost_per_trade > 0 and (plan["entry"] or plan["exit"]):
                tc = cost_per_trade

            if pd.notna(top_ret) and pd.notna(bot_ret):
                ls_returns.append(top_ret - bot_ret - 2 * tc)
            if pd.notna(top_ret):
                lo_returns.append(top_ret - tc)

        ls_ret = np.mean(ls_returns) if ls_returns else np.nan
        lo_ret = np.mean(lo_returns) if lo_returns else np.nan

        results.append({
            "date"             : date,
            "long_short_return": ls_ret,
            "long_only_return" : lo_ret,
            "n_portfolios"     : len(active),
        })

    return pd.DataFrame(results).set_index("date")


def compute_benchmark(prices):
    """
    Equal-weighted VN30 benchmark return each month.
    Uses point-in-time constituents.
    Fallback if ETF benchmark download fails.
    """
    monthly_returns = prices.pct_change()
    benchmark       = []
    periods         = sorted(VN30_CONSTITUENTS.keys())

    for i, period in enumerate(periods):
        constituents = VN30_CONSTITUENTS[period]
        year, month  = period.split("-")
        start = pd.Timestamp(f"{year}-{month}-01")
        end   = (
            pd.Timestamp(f"{periods[i+1].split('-')[0]}-"
                         f"{periods[i+1].split('-')[1]}-01")
            if i + 1 < len(periods)
            else pd.Timestamp("2025-01-31")
        )

        dates = monthly_returns.index[
            (monthly_returns.index >= start) &
            (monthly_returns.index <  end)
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
    bm.name = "Benchmark"
    return bm


if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")

    prices = pd.read_csv(
        "data/processed/prices.csv",
        index_col=0, parse_dates=True
    )
    print(f"Loaded: {prices.shape}")

    # Test with 3-month formation, 1 skip, 6-month holding, no costs
    print("\nBuilding portfolios (3-1-6, no cost)...")
    port = build_portfolios(prices, formation=3, skip=1, holding=6,
                            cost_per_trade=0.0)

    print(f"Portfolio months: {len(port)}")
    print(f"Period: {port.index[0].date()} to {port.index[-1].date()}")
    print(f"\nSample (last 6 months):")
    print(port[["long_short_return", "long_only_return",
                "n_portfolios"]].tail(6).round(4))

    # Benchmark
    bm = compute_benchmark(prices)
    print(f"\nBenchmark months: {len(bm)}")
    print(f"Sample (last 6 months):")
    print(bm.tail(6).round(4))