import pandas as pd
import numpy as np
import yfinance as yf
import os
import glob

# ── Point-in-time VN30 constituents ────────────────────────────────────────────
# Source: HOSE official announcements
# Rebalanced every January and July (effective 4th Monday)

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
    date   = pd.Timestamp(date)
    year   = date.year
    month  = date.month
    key    = f"{year}-01" if month < 7 else f"{year}-07"

    # Fall back to most recent available period if key not found
    periods = sorted(VN30_CONSTITUENTS.keys())
    while key not in VN30_CONSTITUENTS:
        idx = periods.index(key) - 1 if key in periods else -1
        key = periods[max(idx, 0)]

    return VN30_CONSTITUENTS[key], VN30_RESERVES.get(key, [])

def download_prices(symbols, start="2015-01-01", end="2024-12-31"):
    """
    Download monthly adjusted close prices from Yahoo Finance.
    Downloads in batches of 15 to avoid rate limiting.
    Returns DataFrame: dates as index, tickers as columns.
    """
    yf_symbols = [s + ".VN" for s in symbols]
    all_prices  = []
    batch_size  = 15
    batches     = [
        yf_symbols[i:i + batch_size]
        for i in range(0, len(yf_symbols), batch_size)
    ]

    for i, batch in enumerate(batches):
        tickers_clean = [s.replace(".VN", "") for s in batch]
        print(f"Batch {i+1}/{len(batches)}: {tickers_clean}")
        try:
            raw = yf.download(
                tickers     = batch,
                start       = start,
                end         = end,
                interval    = "1mo",
                auto_adjust = True,
                progress    = False
            )
            if raw.empty:
                print(f"  No data returned")
                continue

            # Handle single vs multi ticker response
            if isinstance(raw.columns, pd.MultiIndex):
                prices = raw["Close"].copy()
            else:
                prices = raw[["Close"]].copy()
                prices.columns = [batch[0].replace(".VN", "")]

            prices.columns = [c.replace(".VN", "") for c in prices.columns]
            all_prices.append(prices)

        except Exception as e:
            print(f"  Batch failed: {e}")

    if not all_prices:
        raise ValueError("No data downloaded from Yahoo Finance.")

    combined = pd.concat(all_prices, axis=1)
    combined = combined.loc[:, ~combined.columns.duplicated()]
    combined.index = pd.to_datetime(combined.index)
    return combined.sort_index()

def load_manual_prices(raw_dir="data/raw"):
    """
    Load manually downloaded Excel files from cafef.vn.
    Each file must be named TICKER.xlsx and contain:
      - 'Ngay' or 'Ngày' column for dates
      - 'Gia dieu chinh' or 'Giá điều chỉnh' for adjusted prices
    Returns DataFrame of monthly prices.
    """
    files  = glob.glob(os.path.join(raw_dir, "*.xlsx"))
    prices = {}

    if not files:
        print("  No manual files found in data/raw/")
        return pd.DataFrame()

    for f in files:
        ticker = os.path.basename(f).replace(".xlsx", "").upper()
        try:
            df = pd.read_excel(f)

            # Find date column
            date_col = next(
                (c for c in df.columns if "ng" in c.lower()), None
            )
            # Find adjusted price column
            price_col = next(
                (c for c in df.columns if "u ch" in c.lower()), None
            )

            if date_col is None or price_col is None:
                print(f"  ✗ {ticker}: cannot find date/price columns "
                      f"— columns are: {df.columns.tolist()}")
                continue

            df[date_col]  = pd.to_datetime(df[date_col], dayfirst=True)
            series        = df.set_index(date_col)[price_col].sort_index()
            series        = series.resample("ME").last()
            prices[ticker] = series
            print(f"  ✓ {ticker}: {len(series)} months from cafef")

        except Exception as e:
            print(f"  ✗ {ticker}: {e}")

    return pd.DataFrame(prices) if prices else pd.DataFrame()

def check_vn30_coverage(prices):
    """
    Check data coverage per VN30 rebalancing period.
    Only checks stocks during the periods they were actually in VN30.
    This is the correct survivorship-bias-free coverage check.
    """
    periods = sorted(VN30_CONSTITUENTS.keys())

    print(f"\n{'='*60}")
    print("VN30 Point-in-Time Coverage Check")
    print(f"{'='*60}")

    missing_by_period = {}

    for i, period in enumerate(periods):
        constituents = VN30_CONSTITUENTS[period]

        # Active window for this period
        year, month = period.split("-")
        start = pd.Timestamp(f"{year}-{month}-01")
        end   = (
            pd.Timestamp(f"{periods[i+1].split('-')[0]}-"
                         f"{periods[i+1].split('-')[1]}-01")
            if i + 1 < len(periods)
            else pd.Timestamp("2024-12-31")
        )

        window          = prices.loc[(prices.index >= start) &
                                     (prices.index <  end)]
        missing         = []
        sparse          = []

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
                print(f"  ✗ Missing entirely : {missing}")
            if sparse:
                print(f"  ⚠ Sparse (<80%)   : {sparse}")
            missing_by_period[period] = missing
        else:
            print(f"✓ {period}: all {len(constituents)} stocks OK")

    return missing_by_period

def build_price_matrix(start="2015-01-01", end="2024-12-31"):
    """
    Full data pipeline:
    1. Download all VN30 master tickers from Yahoo Finance
    2. Load any manually downloaded cafef files from data/raw/
    3. Merge — cafef data fills gaps where Yahoo Finance fails
    4. Run point-in-time coverage check
    5. Save to data/processed/prices.csv
    """
    print("=" * 60)
    print(f"VN30 Master universe: {len(VN30_MASTER)} tickers")
    print(f"Tickers: {VN30_MASTER}")
    print("=" * 60)

    # Step 1: Yahoo Finance
    print("\nStep 1: Downloading from Yahoo Finance...")
    prices = download_prices(VN30_MASTER, start=start, end=end)

    # Step 2: Manual cafef files
    print("\nStep 2: Loading manual cafef files...")
    manual = load_manual_prices("data/raw")

    # Step 3: Merge
    if not manual.empty:
        print("\nStep 3: Merging Yahoo Finance + cafef...")
        for ticker in manual.columns:
            if ticker in prices.columns:
                # Fill Yahoo gaps with cafef data
                prices[ticker] = prices[ticker].combine_first(manual[ticker])
                print(f"  Merged {ticker}: Yahoo + cafef")
            else:
                # New ticker only available from cafef
                prices[ticker] = manual[ticker]
                print(f"  Added  {ticker}: cafef only")
    else:
        print("\nStep 3: No manual files to merge")

    # Step 4: Coverage check
    missing_by_period = check_vn30_coverage(prices)

    # Step 5: Save
    os.makedirs("data/processed", exist_ok=True)
    prices.to_csv("data/processed/prices.csv")
    print(f"\nSaved to data/processed/prices.csv")
    print(f"Shape: {prices.shape}")
    print(f"Period: {prices.index[0].date()} to {prices.index[-1].date()}")

    # Summary
    all_missing = sorted(set(
        t for tickers in missing_by_period.values() for t in tickers
    ))
    if all_missing:
        print(f"\n{'='*60}")
        print(f"Action required — download from cafef.vn:")
        for t in all_missing:
            print(f"  → {t}")
        print(f"{'='*60}")
    else:
        print("\nAll VN30 constituents have sufficient data!")

    return prices, missing_by_period

if __name__ == "__main__":
    prices, missing_by_period = build_price_matrix(
        start="2015-01-01",
        end  ="2024-12-31"
    )