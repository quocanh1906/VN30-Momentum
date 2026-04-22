import pandas as pd
import numpy as np
import os
import time

# ── Point-in-time VN30 constituents ────────────────────────────────────────────
VN30_CONSTITUENTS = {
    "2018-01": ["BID","BMP","BVH","CII","CTD","CTG","DHG","DPM","FPT","GAS","GMD","HPG","HSG","KDC","MBB","MSN","MWG","NT2","NVL","PLX","REE","ROS","SAB","SBT","SSI","STB","VCB","VIC","VJC","VNM"],
    "2018-07": ["BMP","CII","CTD","CTG","DHG","DPM","FPT","GAS","GMD","HPG","HSG","KDC","MBB","MSN","MWG","NVL","PLX","PNJ","REE","ROS","SAB","SBT","SSI","STB","VCB","VIC","VJC","VNM","VPB","VRE"],
    "2019-01": ["CII","CTD","CTG","DHG","DPM","EIB","FPT","GAS","GMD","HDB","HPG","MBB","MSN","MWG","NVL","PNJ","REE","ROS","SAB","SBT","SSI","STB","TCB","VCB","VHM","VIC","VJC","VNM","VPB","VRE"],
    "2019-07": ["BID","BVH","CTD","CTG","DPM","EIB","FPT","GAS","GMD","HDB","HPG","MBB","MSN","MWG","NVL","PNJ","REE","ROS","SAB","SBT","SSI","STB","TCB","VCB","VHM","VIC","VJC","VNM","VPB","VRE"],
    "2020-01": ["BID","BVH","CTD","CTG","EIB","FPT","GAS","HDB","HPG","MBB","MSN","MWG","NVL","PLX","PNJ","POW","REE","ROS","SAB","SBT","SSI","STB","TCB","VCB","VHM","VIC","VJC","VNM","VPB","VRE"],
    "2020-07": ["BID","CTG","EIB","FPT","GAS","HDB","HPG","KDH","MBB","MSN","MWG","NVL","PLX","PNJ","POW","REE","ROS","SAB","SBT","SSI","STB","TCB","TCH","VCB","VHM","VIC","VJC","VNM","VPB","VRE"],
    "2021-01": ["BID","BVH","CTG","FPT","GAS","HDB","HPG","KDH","MBB","MSN","MWG","NVL","PDR","PLX","PNJ","POW","REE","SBT","SSI","STB","TCB","TCH","TPB","VCB","VHM","VIC","VJC","VNM","VPB","VRE"],
    "2021-07": ["ACB","BID","BVH","CTG","FPT","GAS","GVR","HDB","HPG","KDH","MBB","MSN","MWG","NVL","PDR","PLX","PNJ","POW","SAB","SSI","STB","TCB","TPB","VCB","VHM","VIC","VJC","VNM","VPB","VRE"],
    "2022-01": ["ACB","BID","BVH","CTG","FPT","GAS","GVR","HDB","HPG","KDH","MBB","MSN","MWG","NVL","PDR","PLX","PNJ","POW","SAB","SSI","STB","TCB","TPB","VCB","VHM","VIC","VJC","VNM","VPB","VRE"],
    "2022-07": ["ACB","BID","BVH","CTG","FPT","GAS","GVR","HDB","HPG","KDH","MBB","MSN","MWG","NVL","PDR","PLX","POW","SAB","SSI","STB","TCB","TPB","VCB","VHM","VIB","VIC","VJC","VNM","VPB","VRE"],
    "2023-01": ["ACB","BCM","BID","BVH","CTG","FPT","GAS","GVR","HDB","HPG","MBB","MSN","MWG","NVL","PDR","PLX","POW","SAB","SSI","STB","TCB","TPB","VCB","VHM","VIB","VIC","VJC","VNM","VPB","VRE"],
    "2023-07": ["ACB","BCM","BID","BVH","CTG","FPT","GAS","GVR","HDB","HPG","MBB","MSN","MWG","PLX","POW","SAB","SHB","SSB","SSI","STB","TCB","TPB","VCB","VHM","VIB","VIC","VJC","VNM","VPB","VRE"],
    "2024-01": ["ACB","BCM","BID","BVH","CTG","FPT","GAS","GVR","HDB","HPG","MBB","MSN","MWG","PLX","POW","SAB","SHB","SSB","SSI","STB","TCB","TPB","VCB","VHM","VIB","VIC","VJC","VNM","VPB","VRE"],
    "2024-07": ["ACB","BCM","BID","BVH","CTG","FPT","GAS","GVR","HDB","HPG","MBB","MSN","MWG","PLX","POW","SAB","SHB","SSB","SSI","STB","TCB","TPB","VCB","VHM","VIB","VIC","VJC","VNM","VPB","VRE"],
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

VN30_MASTER = sorted(set(
    ticker
    for tickers in list(VN30_CONSTITUENTS.values()) +
                   list(VN30_RESERVES.values())
    for ticker in tickers
))

# ── ROS manual data ─────────────────────────────────────────────────────────────
# Source: cafef.vn — first day of month prices, shifted to previous month-end
# ROS (FLC Faros) — data unavailable from vnstock due to FLC fraud scandal
# Manually sourced and shifted by one month to approximate month-end prices

ROS_PRICES = {
    "2016-12-31": 98106.0,
    "2017-01-31": 112803.0,
    "2017-02-28": 124318.1,
    "2017-03-31": 122727.2,
    "2017-04-30": 100000.0,
    "2017-05-31": 67045.4,
    "2017-06-30": 76250.0,
    "2017-07-31": 92500.0,
    "2017-08-31": 89250.0,
    "2017-09-30": 166666.6,
    "2017-10-31": 148083.3,
    "2017-11-30": 151416.6,
    "2017-12-31": 145333.3,
    "2018-01-31": 114333.3,
    "2018-02-28": 112500.0,
    "2018-03-31": 71666.6,
    "2018-04-30": 60700.0,
    "2018-05-31": 43000.0,
    "2018-06-30": 42600.0,
    "2018-07-31": 41200.0,
    "2018-08-31": 40300.0,
    "2018-09-30": 38150.0,
    "2018-10-31": 36000.0,
    "2018-11-30": 38700.0,
    "2018-12-31": 31450.0,
    "2019-01-31": 34650.0,
    "2019-02-28": 32000.0,
    "2019-03-31": 30850.0,
    "2019-04-30": 29950.0,
    "2019-05-31": 29800.0,
    "2019-06-30": 27150.0,
    "2019-07-31": 28000.0,
    "2019-08-31": 26400.0,
    "2019-09-30": 25100.0,
    "2019-10-31": 24300.0,
    "2019-11-30": 17300.0,
    "2019-12-31": 9330.0,
    "2020-01-31": 7260.0,
    "2020-02-29": 3260.0,
    "2020-03-31": 3760.0,
    "2020-04-30": 3500.0,
    "2020-05-31": 2970.0,
    "2020-06-30": 2090.0,
    "2020-07-31": 2220.0,
    "2020-08-31": 2170.0,
    "2020-09-30": 2200.0,
    "2020-10-31": 2180.0,
    "2020-11-30": 2530.0,
    "2020-12-31": 4480.0,
    "2021-01-31": 3400.0,
    "2021-02-28": 4820.0,
    "2021-03-31": 6440.0,
    "2021-04-30": 6530.0,
    "2021-05-31": 6550.0,
    "2021-06-30": 4970.0,
    "2021-07-31": 4970.0,
    "2021-08-31": 5250.0,
    "2021-09-30": 5600.0,
    "2021-10-31": 6930.0,
    "2021-11-30": 13600.0,
    "2021-12-31": 7090.0,
    "2022-01-31": 8200.0,
    "2022-02-28": 7060.0,
    "2022-03-31": 5310.0,
    "2022-04-30": 4110.0,
    "2022-05-31": 2880.0,
    "2022-06-30": 2890.0,
    "2022-07-31": 2510.0,
}


def get_ros_series():
    """Return ROS as a monthly price Series."""
    ros = pd.Series(ROS_PRICES)
    ros.index = pd.to_datetime(ros.index)
    ros.name = "ROS"
    return ros


def download_single_vnstock(symbol, start="2015-01-01", end="2024-12-31",
                             retries=3, delay=5):
    """
    Download single stock monthly prices from vnstock with retry.
    Rate limit: 3 seconds between requests.
    """
    from vnstock import Quote

    for attempt in range(retries):
        try:
            quote = Quote(symbol=symbol, source='KBS')
            df    = quote.history(start=start, end=end, interval='1D')

            if df is None or df.empty:
                return None

            df['time'] = pd.to_datetime(df['time'])
            df = df.set_index('time')['close'].sort_index()

            # Resample daily to monthly end-of-month
            df = df.resample('ME').last().dropna()

            # Deduplicate just in case
            df = df[~df.index.duplicated(keep='last')]
            df.name = symbol
            return df

        except Exception as e:
            if attempt < retries - 1:
                print(f"  ↻ {symbol} attempt {attempt+1} failed: {e} — retrying in {delay}s")
                time.sleep(delay)
            else:
                print(f"  ✗ {symbol}: {e}")
                return None


def download_all_vnstock(symbols, start="2015-01-01", end="2024-12-31",
                          delay=3, batch_pause=60, batch_size=15):
    """
    Download all symbols with rate limiting.
    Rate limit: 3s between requests, 60s pause every 15 requests.
    """
    results = {}
    failed  = []
    total   = len(symbols)

    # Skip ROS — handled separately from hardcoded data
    symbols = [s for s in symbols if s != "ROS"]

    print(f"\nDownloading {len(symbols)} tickers from vnstock...")
    print(f"Estimated time: ~{(len(symbols)*delay + (len(symbols)//batch_size)*batch_pause)//60+1} mins\n")

    for i, symbol in enumerate(symbols):
        print(f"[{i+1}/{len(symbols)}] {symbol}...", end=" ", flush=True)
        series = download_single_vnstock(symbol, start, end)

        if series is not None and not series.empty:
            results[symbol] = series
            print(f"✓ {len(series)} months")
        else:
            failed.append(symbol)
            print("✗ no data")

        if (i + 1) % batch_size == 0 and i + 1 < len(symbols):
            print(f"\n  --- Pausing {batch_pause}s to reset rate limit ---\n")
            time.sleep(batch_pause)
        else:
            time.sleep(delay)

    if failed:
        print(f"\nFailed ({len(failed)}): {failed}")

    return pd.DataFrame(results), failed


def check_vn30_coverage(prices):
    """Check data coverage per VN30 rebalancing period."""
    periods = sorted(VN30_CONSTITUENTS.keys())
    print(f"\n{'='*60}")
    print("VN30 Point-in-Time Coverage Check")
    print(f"{'='*60}")
    missing_by_period = {}

    for i, period in enumerate(periods):
        constituents = VN30_CONSTITUENTS[period]
        year, month  = period.split("-")
        start = pd.Timestamp(f"{year}-{month}-01")
        end   = (
            pd.Timestamp(f"{periods[i+1].split('-')[0]}-"
                         f"{periods[i+1].split('-')[1]}-01")
            if i + 1 < len(periods)
            else pd.Timestamp("2024-12-31")
        )
        window  = prices.loc[(prices.index >= start) & (prices.index < end)]
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
            print(f"\n❌ {period} ({start.date()} → {end.date()}):")
            if missing: print(f"   Missing: {missing}")
            if sparse:  print(f"   Sparse : {sparse}")
            missing_by_period[period] = missing
        else:
            print(f"✓  {period}: all {len(constituents)} stocks OK")

    return missing_by_period


def download_etf_benchmark(symbol="E1VFVN30", start="2015-01-01",
                            end="2024-12-31"):
    """
    Download monthly E1VFVN30 ETF returns as benchmark.
    More realistic than equal-weighted constituent returns.
    """
    from vnstock import Quote

    print(f"  Downloading {symbol} ETF benchmark...")
    try:
        quote = Quote(symbol=symbol, source='KBS')
        df    = quote.history(start=start, end=end, interval='1D')

        if df is None or df.empty:
            print(f"  ✗ {symbol}: no data")
            return None

        df['time'] = pd.to_datetime(df['time'])
        df = df.set_index('time')['close'].sort_index()
        df = df.resample('ME').last().dropna()

        returns       = df.pct_change().dropna()
        returns.index = pd.to_datetime(
            returns.index.to_period('M').to_timestamp('M')
        )
        returns = returns[~returns.index.duplicated()]
        returns.name = "Benchmark (E1VFVN30)"

        print(f"  ✓ {symbol}: {len(returns)} months "
              f"({returns.index[0].date()} to {returns.index[-1].date()})")
        return returns

    except Exception as e:
        print(f"  ✗ {symbol}: {e}")
        return None


def build_price_matrix(start="2015-01-01", end="2024-12-31"):
    """
    Full data pipeline:
    1. Download all VN30 tickers from vnstock
    2. Inject hardcoded ROS data
    3. Coverage check
    4. Save to data/processed/prices.csv
    """
    print("=" * 60)
    print(f"VN30 Master universe: {len(VN30_MASTER)} tickers")
    print("=" * 60)

    prices, failed = download_all_vnstock(VN30_MASTER, start=start, end=end)

    # Inject ROS from hardcoded manual data
    print("\nInjecting ROS manual data...")
    ros = get_ros_series()
    prices["ROS"] = ros
    print(f"  ✓ ROS: {ros.notna().sum()} months injected")

    if prices.empty:
        raise ValueError("No data downloaded.")

    missing_by_period = check_vn30_coverage(prices)

    os.makedirs("data/processed", exist_ok=True)
    prices.to_csv("data/processed/prices.csv")
    print(f"\nSaved: {prices.shape}")
    print(f"Period: {prices.index[0].date()} to {prices.index[-1].date()}")

    return prices, missing_by_period


if __name__ == "__main__":
    prices, missing = build_price_matrix(
        start="2015-01-01",
        end  ="2024-12-31"
    )