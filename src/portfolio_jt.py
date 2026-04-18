import pandas as pd
import numpy as np
from data import VN30_CONSTITUENTS, VN30_RESERVES

def build_jt_portfolios(prices, formation=12, skip=1, holding=6):
    """
    Jegadeesh-Titman (1993) overlapping momentum portfolios.

    Methodology:
    - Every month t, form a new portfolio based on past 'formation' months
      of returns, skipping the most recent 'skip' month
    - Hold each portfolio for 'holding' months
    - Monthly return = equal-weighted average across all overlapping
      portfolios currently being held

    For a holding period of H months, at any month t we hold H portfolios:
    - Portfolio formed at t-1 (in month 1 of H-month hold)
    - Portfolio formed at t-2 (in month 2 of H-month hold)
    - ...
    - Portfolio formed at t-H (in month H of H-month hold)

    Parameters
    ----------
    prices    : DataFrame, monthly prices
    formation : int, momentum lookback in months (default 12)
    skip      : int, months to skip (default 1)
    holding   : int, holding period in months (default 6)

    Returns
    -------
    DataFrame with columns: long_short_return, long_only_return,
                            n_top, n_bottom
    """
    monthly_returns = prices.pct_change()
    periods         = sorted(VN30_CONSTITUENTS.keys())

    # Step 1: compute momentum signal for every month
    momentum = (
        monthly_returns
        .shift(skip)
        .rolling(formation)
        .apply(lambda x: (1 + x).prod() - 1, raw=True)
    )

    # Step 2: for each month, form a portfolio and store its
    # planned returns for the next H months
    # portfolio_plans[t] = {month: {top: [...], bottom: [...]}}
    portfolio_plans = {}

    for i, signal_date in enumerate(momentum.index):

        # Skip if no signal yet
        row = momentum.loc[signal_date]
        if row.isna().all():
            continue

        # Get point-in-time VN30 constituents
        year  = signal_date.year
        month = signal_date.month
        key   = f"{year}-01" if month < 7 else f"{year}-07"

        if key not in VN30_CONSTITUENTS:
            available = [p for p in periods if p <= key]
            if not available:
                continue
            key = available[-1]

        constituents = VN30_CONSTITUENTS[key]
        reserves     = VN30_RESERVES.get(key, [])

        # Get momentum scores for active constituents
        scores = row[[t for t in constituents if t in row.index]]
        scores = scores.dropna()

        if len(scores) < 6:
            continue

        # Rank into terciles
        try:
            labels = pd.qcut(scores, q=3, labels=["bottom","mid","top"])
        except ValueError:
            continue

        top    = labels[labels == "top"].index.tolist()
        bottom = labels[labels == "bottom"].index.tolist()

        # Plan this portfolio for next H months
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
                "key"     : key,
            })

    # Step 3: for each month, average returns across all active portfolios
    results = []

    for date in monthly_returns.index:
        if date not in portfolio_plans:
            continue

        active_portfolios = portfolio_plans[date]
        next_returns      = monthly_returns.loc[date]

        ls_returns = []
        lo_returns = []

        for plan in active_portfolios:
            top      = plan["top"]
            bottom   = plan["bottom"]
            reserves = plan["reserves"]

            # Handle suspended stocks
            active_top    = []
            active_bottom = []

            for ticker in top:
                if ticker in next_returns.index and pd.notna(next_returns[ticker]):
                    active_top.append(ticker)
                else:
                    for r in reserves:
                        if (r not in top + bottom and
                            r in next_returns.index and
                            pd.notna(next_returns[r])):
                            active_top.append(r)
                            break

            for ticker in bottom:
                if ticker in next_returns.index and pd.notna(next_returns[ticker]):
                    active_bottom.append(ticker)
                else:
                    for r in reserves:
                        if (r not in top + bottom + active_top and
                            r in next_returns.index and
                            pd.notna(next_returns[r])):
                            active_bottom.append(r)
                            break

            top_ret = next_returns[active_top].mean() if active_top else np.nan
            bot_ret = next_returns[active_bottom].mean() if active_bottom else np.nan

            if pd.notna(top_ret) and pd.notna(bot_ret):
                ls_returns.append(top_ret - bot_ret)
            if pd.notna(top_ret):
                lo_returns.append(top_ret)

        # Average across all overlapping portfolios
        ls_ret = np.mean(ls_returns) if ls_returns else np.nan
        lo_ret = np.mean(lo_returns) if lo_returns else np.nan

        results.append({
            "date"             : date,
            "long_short_return": ls_ret,
            "long_only_return" : lo_ret,
            "n_portfolios"     : len(active_portfolios),
        })

    return pd.DataFrame(results).set_index("date")

