import pandas as pd
import numpy as np
import os
import glob
import time

# ── Point-in-time VN30 constituents ────────────────────────────────────────────
# Source: HOSE official announcements (all periods verified from official docs)

VN30_CONSTITUENTS = {
    # 22/01/2018 - 20/07/2018
    "2018-01": [
        "BID","BMP","BVH","CII","CTD","CTG","DHG","DPM","FPT",
        "GAS","GMD","HPG","HSG","KDC","MBB","MSN","MWG","NT2",
        "NVL","PLX","REE","ROS","SAB","SBT","SSI","STB","VCB",
        "VIC","VJC","VNM"
    ],
    # 23/07/2018 - 25/01/2019
    "2018-07": [
        "BMP","CII","CTD","CTG","DHG","DPM","FPT","GAS","GMD",
        "HPG","HSG","KDC","MBB","MSN","MWG","NVL","PLX","PNJ",
        "REE","ROS","SAB","SBT","SSI","STB","VCB","VIC","VJC",
        "VNM","VPB","VRE"
    ],
    # 11/02/2019 - 02/08/2019
    "2019-01": [
        "CII","CTD","CTG","DHG","DPM","EIB","FPT","GAS","GMD",
        "HDB","HPG","MBB","MSN","MWG","NVL","PNJ","REE","ROS",
        "SAB","SBT","SSI","STB","TCB","VCB","VHM","VIC","VJC",
        "VNM","VPB","VRE"
    ],
    # 05/08/2019 - 31/01/2020
    "2019-07": [
        "BID","BVH","CTD","CTG","DPM","EIB","FPT","GAS","GMD",
        "HDB","HPG","MBB","MSN","MWG","NVL","PNJ","REE","ROS",
        "SAB","SBT","SSI","STB","TCB","VCB","VHM","VIC","VJC",
        "VNM","VPB","VRE"
    ],
    # 03/02/2020 - 31/07/2020
    "2020-01": [
        "BID","BVH","CTD","CTG","EIB","FPT","GAS","HDB","HPG",
        "MBB","MSN","MWG","NVL","PLX","PNJ","POW","REE","ROS",
        "SAB","SBT","SSI","STB","TCB","VCB","VHM","VIC","VJC",
        "VNM","VPB","VRE"
    ],
    # 07/2020 - 01/2021
    "2020-07": [
        "BID","CTG","EIB","FPT","GAS","HDB","HPG","KDH","MBB",
        "MSN","MWG","NVL","PLX","PNJ","POW","REE","ROS","SAB",
        "SBT","SSI","STB","TCB","TCH","VCB","VHM","VIC","VJC",
        "VNM","VPB","VRE"
    ],
    # 01/2021 - 07/2021
    "2021-01": [
        "BID","BVH","CTG","FPT","GAS","HDB","HPG","KDH","MBB",
        "MSN","MWG","NVL","PDR","PLX","PNJ","POW","REE","SBT",
        "SSI","STB","TCB","TCH","TPB","VCB","VHM","VIC","VJC",
        "VNM","VPB","VRE"
    ],
    # 07/2021 - 01/2022
    "2021-07": [
        "ACB","BID","BVH","CTG","FPT","GAS","GVR","HDB","HPG",
        "KDH","MBB","MSN","MWG","NVL","PDR","PLX","PNJ","POW",
        "SAB","SSI","STB","TCB","TPB","VCB","VHM","VIC","VJC",
        "VNM","VPB","VRE"
    ],
    # 07/02/2022 - 07/2022
    "2022-01": [
        "ACB","BID","BVH","CTG","FPT","GAS","GVR","HDB","HPG",
        "KDH","MBB","MSN","MWG","NVL","PDR","PLX","PNJ","POW",
        "SAB","SSI","STB","TCB","TPB","VCB","VHM","VIC","VJC",
        "VNM","VPB","VRE"
    ],
    # 07/2022 - 01/2023
    "2022-07": [
        "ACB","BID","BVH","CTG","FPT","GAS","GVR","HDB","HPG",
        "KDH","MBB","MSN","MWG","NVL","PDR","PLX","POW","SAB",
        "SSI","STB","TCB","TPB","VCB","VHM","VIB","VIC","VJC",
        "VNM","VPB","VRE"
    ],
    # 01/2023 - 07/2023
    "2023-01": [
        "ACB","BCM","BID","BVH","CTG","FPT","GAS","GVR","HDB",
        "HPG","MBB","MSN","MWG","NVL","PDR","PLX","POW","SAB",
        "SSI","STB","TCB","TPB","VCB","VHM","VIB","VIC","VJC",
        "VNM","VPB","VRE"
    ],
    # 07/08/2023 - 02/02/2024
    "2023-07": [
        "ACB","BCM","BID","BVH","CTG","FPT","GAS","GVR","HDB",
        "HPG","MBB","MSN","MWG","PLX","POW","SAB","SHB","SSB",
        "SSI","STB","TCB","TPB","VCB","VHM","VIB","VIC","VJC",
        "VNM","VPB","VRE"
    ],
    # 01/2024 - 07/2024
    "2024-01": [
        "ACB","BCM","BID","BVH","CTG","FPT","GAS","GVR","HDB",
        "HPG","MBB","MSN","MWG","PLX","POW","SAB","SHB","SSB",
        "SSI","STB","TCB","TPB","VCB","VHM","VIB","VIC","VJC",
        "VNM","VPB","VRE"
    ],
    # 05/08/2024 - 24/01/2025
    "2024-07": [
        "ACB","BCM","BID","BVH","CTG","FPT","GAS","GVR","HDB",
        "HPG","MBB","MSN","MWG","PLX","POW","SAB","SHB","SSB",
        "SSI","STB","TCB","TPB","VCB","VHM","VIB","VIC","VJC",
        "VNM","VPB","VRE"
    ],
}

VN30_RESERVES = {
    "2018-01": ["PNJ","HNG","HT1","HAG","KBC"],
    "2018-07": ["VCI","DXG","PDR","HCM","TCH"],
    "2019-01": ["VCI","DXG","PDR","HCM","TCH"],
    "2019-07": ["TPB","GEX","DXG","VHC","TCH"],
    "2020-01": ["TPB","GEX","PDR","KBC","DXG"],
    "2020-07": ["GEX","PDR","PHR","KBC","DXG"],
    "2021-01": ["GEX","PHR","KBC","VHC","VPI"],
    "2021-07": ["VIB","MSB","OCB","EIB","DGC"],
    "2022-01": ["VIB","SSB","OCB","MSB","EIB"],
    "2022-07": ["SSB","SHB","EIB","MSB","OCB"],
    "2023-01": ["SSB","SHB","EIB","DGC","MSB"],
    "2023-07": ["EIB","PNJ","REE","DGC","MSB"],
    "2024-01": ["EIB","PNJ","REE","DGC","MSB"],
    "2024-07": ["LPB","DGC","EIB","NVL","PNJ"],
}

# All unique tickers ever in VN30 or reserve list
VN30_MASTER = sorted(set(
    ticker
    for tickers in list(VN30_CONSTITUENTS.values()) +
                   list(VN30_RESERVES.values())
    for ticker in tickers
))

def get_active_constituents(date):
    """
    Return the VN30 constituent list active on a given date.
    VN30 is rebalanced in January and July each year.
    """
    date  = pd.Timestamp(date)
    year  = date.year
    month = date.month
    key   = f"{year}-01" if month < 7 else f"{year}-07"

    periods = sorted(VN30_CONSTITUENTS.keys())
    if key not in VN30_CONSTITUENTS:
        # Fall back to most recent available period
        available = [p for p in periods if p <= key]
        key = available[-1] if available else periods[0]

    return VN30_CONSTITUENTS[key], VN30_RESERVES.get(key, [])

def download_single_vnstock(symbol, start="2015-01-01", end="2024-12-31"):
    """
    Download single stock history from vnstock (KBS source).
    Returns a monthly close price Series or None if failed.
    """
    try:
        from vnstock import Quote
        quote = Quote(symbol=symbol, source='KBS')
        df    = quote.history(start=start, end=end, interval='1M')

        if df is None or df.empty:
            return None

        df['time'] = pd.to_datetime(df['time'])
        df = df.set_index('time')['close']
        df = df.sort_index()
        df.name = symbol
        return df

    except Exception as e:
        print(f"  ✗ {symbol}: {e}")
        return None

def download_all_vnstock(symbols, start="2015-01-01", end="2024-12-31",
                          delay=3, batch_pause=60, batch_size=15):
    """
    Download all symbols from vnstock with rate limiting.
    
    Rate limit: 20 requests/minute → 1 request every 3 seconds
    Every batch_size requests, pause batch_pause seconds to reset window.
    
    At 3s/stock + 60s pause every 15 stocks:
    ~65 tickers takes approximately 5-6 minutes total.
    """
    results = {}
    total   = len(symbols)
    failed  = []

    print(f"\nDownloading {total} tickers from vnstock (KBS)...")
    print(f"Rate limit: {delay}s between requests, "
          f"{batch_pause}s pause every {batch_size} requests")
    print(f"Estimated time: ~{(total * delay + (total // batch_size) * batch_pause) // 60 + 1} minutes\n")

    for i, symbol in enumerate(symbols):
        print(f"[{i+1}/{total}] {symbol}...", end=" ", flush=True)
        series = download_single_vnstock(symbol, start, end)

        if series is not None and not series.empty:
            results[symbol] = series
            print(f"✓ {len(series)} months")
        else:
            failed.append(symbol)
            print("✗ no data")

        # Rate limiting
        if (i + 1) % batch_size == 0 and i + 1 < total:
            print(f"\n  --- Batch complete, pausing {batch_pause}s "
                  f"to reset rate limit ---\n")
            time.sleep(batch_pause)
        else:
            time.sleep(delay)

    if failed:
        print(f"\nFailed ({len(failed)}): {failed}")

    return pd.DataFrame(results), failed

def check_vn30_coverage(prices):
    """
    Check data coverage per VN30 rebalancing period.
    Only checks stocks during the periods they were actually in VN30.
    """
    periods = sorted(VN30_CONSTITUENTS.keys())

    print(f"\n{'='*60}")
    print("VN30 Point-in-Time Coverage Check")
    print(f"{'='*60}")

    missing_by_period = {}

    for i, period in enumerate(periods):
        constituents = VN30_CONSTITUENTS[period]

        year, month = period.split("-")
        start = pd.Timestamp(f"{year}-{month}-01")
        end   = (
            pd.Timestamp(f"{periods[i+1].split('-')[0]}-"
                         f"{periods[i+1].split('-')[1]}-01")
            if i + 1 < len(periods)
            else pd.Timestamp("2024-12-31")
        )

        window  = prices.loc[(prices.index >= start) &
                              (prices.index <  end)]
        missing = []
        sparse  = []

        for ticker in constituents:
            if ticker not in prices.columns:
                missing.append(ticker)
            else:
                cov = window[ticker].notna().mean()
                if cov < 0.8:
                    sparse.append((ticker, round(cov * 100, 1)))

        if missing or sparse:
            print(f"\n{period}  ({start.date()} → {end.date()}):")
            if missing:
                print(f"  ✗ Missing: {missing}")
            if sparse:
                print(f"  ⚠ Sparse : {sparse}")
            missing_by_period[period] = missing
        else:
            print(f"✓ {period}: all {len(constituents)} stocks OK")

    return missing_by_period

def build_price_matrix(start="2015-01-01", end="2024-12-31"):
    """
    Full data pipeline:
    1. Download all VN30 master tickers from vnstock
    2. Run point-in-time coverage check
    3. Save to data/processed/prices.csv
    """
    print("=" * 60)
    print(f"VN30 Master universe: {len(VN30_MASTER)} tickers")
    print(f"Tickers: {VN30_MASTER}")
    print("=" * 60)

    # Download all from vnstock
    prices, failed = download_all_vnstock(
        VN30_MASTER, start=start, end=end
    )

    if prices.empty:
        raise ValueError("No data downloaded.")

    # Coverage check
    missing_by_period = check_vn30_coverage(prices)

    # Save
    os.makedirs("data/processed", exist_ok=True)
    prices.to_csv("data/processed/prices.csv")
    print(f"\nSaved to data/processed/prices.csv")
    print(f"Shape : {prices.shape}")
    print(f"Period: {prices.index[0].date()} to {prices.index[-1].date()}")

    # Summary
    all_missing = sorted(set(
        t for tickers in missing_by_period.values()
        for t in tickers
    ))
    if all_missing:
        print(f"\nStill missing after download:")
        for t in all_missing:
            print(f"  → {t}")
    else:
        print("\nAll VN30 constituents have sufficient data!")

    return prices, missing_by_period

if __name__ == "__main__":
    prices, missing_by_period = build_price_matrix(
        start="2015-01-01",
        end  ="2024-12-31"
    )