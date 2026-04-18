import pandas as pd
import numpy as np

# ── VN30 constituent data ───────────────────────────────────────────────────────
# Import from data.py so signals.py has access to point-in-time lists
from data import VN30_CONSTITUENTS, VN30_RESERVES

# VN30 rebalancing dates (effective dates from HOSE announcements)
VN30_REBALANCE_DATES = {
    "2018-01": pd.Timestamp("2018-01-22"),
    "2018-07": pd.Timestamp("2018-07-23"),
    "2019-01": pd.Timestamp("2019-02-11"),
    "2019-07": pd.Timestamp("2019-08-05"),
    "2020-01": pd.Timestamp("2020-02-03"),
    "2020-07": pd.Timestamp("2020-08-03"),  # approximate
    "2021-01": pd.Timestamp("2021-02-01"),  # approximate
    "2021-07": pd.Timestamp("2021-08-02"),  # approximate
    "2022-01": pd.Timestamp("2022-02-07"),
    "2022-07": pd.Timestamp("2022-08-01"),  # approximate
    "2023-01": pd.Timestamp("2023-02-06"),  # approximate
    "2023-07": pd.Timestamp("2023-08-07"),
    "2024-01": pd.Timestamp("2024-02-05"),  # approximate
    "2024-07": pd.Timestamp("2024-08-05"),
}

def compute_momentum(prices, lookback=12, skip=1):
    """
    Compute 12-1 momentum signal for each stock each month.

    Standard Jegadeesh-Titman (1993) momentum:
    - Lookback: 12 months of cumulative return
    - Skip: most recent 1 month to avoid short-term reversal

    For each month t, signal = cumulative return from t-12 to t-1

    Parameters
    ----------
    prices   : DataFrame, monthly prices (rows=dates, cols=tickers)
    lookback : int, number of months for momentum window (default 12)
    skip     : int, months to skip at end (default 1)

    Returns
    -------
    DataFrame of momentum scores, same shape as prices
    """
    # Monthly returns
    returns = prices.pct_change()

    # 12-1 momentum: skip most recent month, then compound over lookback
    momentum = (
        returns
        .shift(skip)                          # skip most recent month
        .rolling(lookback)                    # 12 month window
        .apply(lambda x: (1 + x).prod() - 1, # compound returns
               raw=True)
    )

    return momentum

def get_period_key(date):
    """
    Given a date, return the active VN30 period key (e.g. '2021-07').
    """
    date  = pd.Timestamp(date)
    year  = date.year
    month = date.month
    key   = f"{year}-01" if month < 7 else f"{year}-07"

    periods = sorted(VN30_CONSTITUENTS.keys())
    if key not in VN30_CONSTITUENTS:
        available = [p for p in periods if p <= key]
        key = available[-1] if available else periods[0]

    return key

def rank_momentum_at_rebalance(momentum, rebalance_date):
    """
    At a given rebalance date, rank VN30 constituents by momentum
    into terciles using only the active VN30 universe.

    Returns
    -------
    dict with keys: 'top', 'mid', 'bottom', 'all_scores'
    """
    period_key   = get_period_key(rebalance_date)
    constituents = VN30_CONSTITUENTS[period_key]
    reserves     = VN30_RESERVES.get(period_key, [])

    # Find closest available date in momentum index
    available_dates = momentum.index[momentum.index <= rebalance_date]
    if len(available_dates) == 0:
        return None
    signal_date = available_dates[-1]

    # Get momentum scores for active constituents only
    scores = momentum.loc[signal_date, 
                          [t for t in constituents if t in momentum.columns]]
    scores = scores.dropna()

    if len(scores) < 6:
        print(f"  Warning: only {len(scores)} stocks with valid momentum at {signal_date.date()}")
        return None

    # Rank into terciles
    tercile_labels = pd.qcut(scores, q=3, labels=["bottom","mid","top"])

    return {
        "period_key"  : period_key,
        "signal_date" : signal_date,
        "constituents": constituents,
        "reserves"    : reserves,
        "scores"      : scores,
        "terciles"    : tercile_labels,
        "top"         : tercile_labels[tercile_labels == "top"].index.tolist(),
        "mid"         : tercile_labels[tercile_labels == "mid"].index.tolist(),
        "bottom"      : tercile_labels[tercile_labels == "bottom"].index.tolist(),
    }

def build_rebalance_schedule(prices, start="2018-01", end="2024-07"):
    """
    Build the full rebalance schedule with momentum rankings.

    For each VN30 rebalancing period between start and end:
    - Use point-in-time VN30 constituents
    - Compute 12-1 momentum signal
    - Rank into terciles

    Returns
    -------
    List of dicts, one per rebalancing period
    """
    momentum = compute_momentum(prices)
    periods  = sorted(VN30_CONSTITUENTS.keys())
    periods  = [p for p in periods if start <= p <= end]

    schedule = []

    print(f"\n{'='*60}")
    print("VN30 Momentum Rebalance Schedule")
    print(f"{'='*60}")

    for period in periods:
        rebalance_date = VN30_REBALANCE_DATES.get(
            period,
            pd.Timestamp(f"{period[:4]}-{period[5:7]}-15")
        )

        result = rank_momentum_at_rebalance(momentum, rebalance_date)

        if result is None:
            print(f"{period}: insufficient data, skipping")
            continue

        result["period"]         = period
        result["rebalance_date"] = rebalance_date
        schedule.append(result)

        print(f"\n{period} (signal at {result['signal_date'].date()}):")
        print(f"  Universe : {len(result['constituents'])} stocks")
        print(f"  Valid    : {len(result['scores'])} with momentum signal")
        print(f"  Top      : {result['top']}")
        print(f"  Mid      : {result['mid']}")
        print(f"  Bottom   : {result['bottom']}")

    return momentum, schedule
def compare_formation_periods(prices, formations=[3, 6, 9, 12], skip=1):
    """
    Test different momentum formation periods and compare signal strength.
    
    Parameters
    ----------
    prices     : DataFrame, monthly prices
    formations : list of formation periods to test
    skip       : months to skip (default 1)
    
    Returns
    -------
    dict of {formation: momentum DataFrame}
    """
    results = {}
    
    for f in formations:
        print(f"Computing {f}-{skip} momentum...")
        mom = compute_momentum(prices, lookback=f, skip=skip)
        results[f] = mom
    
    return results

if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")

    prices = pd.read_csv(
        "data/processed/prices.csv",
        index_col=0, parse_dates=True
    )
    print(f"Loaded prices: {prices.shape}")
    momentum, schedule = build_rebalance_schedule(prices)
    print(f"\nTotal rebalancing periods: {len(schedule)}")
