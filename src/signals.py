import pandas as pd
import numpy as np
from data import VN30_CONSTITUENTS, VN30_RESERVES


def compute_momentum(prices, lookback=3, skip=1):
    """
    Compute cross-sectional momentum signal at monthly frequency.

    Standard Jegadeesh-Titman momentum:
    - Compounded return over lookback months
    - Skip most recent skip month to avoid short-term reversal

    At month t, signal = compounded return from t-lookback-skip to t-skip

    Parameters
    ----------
    prices   : DataFrame, monthly end-of-month prices
    lookback : int, formation period in months (default 3)
    skip     : int, months to skip (default 1)

    Returns
    -------
    DataFrame of momentum scores, same shape as prices
    """
    returns  = prices.pct_change()
    momentum = (
        returns
        .shift(skip)
        .rolling(lookback)
        .apply(lambda x: (1 + x).prod() - 1, raw=True)
    )
    return momentum


def rank_signals(momentum, date):
    """
    At a given month, rank VN30 constituents by momentum into terciles.

    Parameters
    ----------
    momentum : DataFrame of momentum scores
    date     : the month to rank on

    Returns
    -------
    dict with keys: top, mid, bottom, reserves, scores
    """
    date  = pd.Timestamp(date)
    year  = date.year
    month = date.month
    key   = f"{year}-01" if month < 7 else f"{year}-07"

    periods = sorted(VN30_CONSTITUENTS.keys())
    if key not in VN30_CONSTITUENTS:
        available = [p for p in periods if p <= key]
        key = available[-1] if available else periods[0]

    constituents = VN30_CONSTITUENTS[key]
    reserves     = VN30_RESERVES.get(key, [])

    scores = momentum.loc[date,
                          [t for t in constituents
                           if t in momentum.columns]]
    scores = scores.dropna()

    if len(scores) < 6:
        return None

    try:
        labels = pd.qcut(scores, q=3, labels=["bottom", "mid", "top"])
    except ValueError:
        return None

    return {
        "period_key" : key,
        "constituents": constituents,
        "reserves"   : reserves,
        "scores"     : scores,
        "labels"     : labels,
        "top"        : labels[labels == "top"].index.tolist(),
        "mid"        : labels[labels == "mid"].index.tolist(),
        "bottom"     : labels[labels == "bottom"].index.tolist(),
    }

def validate_momentum_inputs(prices):
    """
    Check data quality for all tickers that feed into momentum computation.
    Unlike the VN30 coverage check which only checks active periods,
    this checks the full price history since gaps anywhere affect
    the rolling momentum calculation.

    Reports:
    - Tickers with large gaps (>3 consecutive missing months)
    - Tickers with sparse overall coverage (<70%)
    - Start dates later than 2016 (won't have 12-month signal by 2018)
    """
    print(f"\n{'='*60}")
    print("Full Price History Quality Check")
    print(f"{'='*60}")

    issues = {}

    for ticker in prices.columns:
        series = prices[ticker]
        total  = len(series)
        valid  = series.notna().sum()
        cov    = valid / total

        # Check coverage
        if cov < 0.70:
            issues[ticker] = issues.get(ticker, [])
            issues[ticker].append(f"Low coverage: {cov*100:.1f}%")

        # Check for large consecutive gaps
        is_null     = series.isna()
        gap_lengths = []
        current_gap = 0
        for val in is_null:
            if val:
                current_gap += 1
            else:
                if current_gap > 0:
                    gap_lengths.append(current_gap)
                current_gap = 0
        if current_gap > 0:
            gap_lengths.append(current_gap)

        max_gap = max(gap_lengths) if gap_lengths else 0
        if max_gap > 3:
            issues[ticker] = issues.get(ticker, [])
            issues[ticker].append(f"Max consecutive gap: {max_gap} months")

        # Check start date — need data before 2017 for 12-month signal by 2018
        first_valid = series.first_valid_index()
        if first_valid is not None and first_valid > pd.Timestamp("2017-01-01"):
            issues[ticker] = issues.get(ticker, [])
            issues[ticker].append(
                f"Late start: {first_valid.date()} "
                f"(need data before 2017-01 for full signal history)"
            )

    if issues:
        print(f"\n⚠ Issues found in {len(issues)} tickers:")
        for ticker, msgs in sorted(issues.items()):
            print(f"\n  {ticker}:")
            for msg in msgs:
                print(f"    → {msg}")
    else:
        print("\n✓ All tickers pass quality check")

    print(f"\n{'='*60}")
    return issues

if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")

    prices = pd.read_csv(
        "data/processed/prices.csv",
        index_col=0, parse_dates=True
    )
    print(f"Loaded: {prices.shape}")

    # Validate full price history before computing momentum
    issues = validate_momentum_inputs(prices)

    for f in [3, 6, 12]:
        mom  = compute_momentum(prices, lookback=f, skip=1)
        last = mom.index[-1]
        rank = rank_signals(mom, last)
        if rank:
            print(f"\n{f}-1 momentum at {last.date()}:")
            print(f"  Top   : {rank['top']}")
            print(f"  Bottom: {rank['bottom']}")