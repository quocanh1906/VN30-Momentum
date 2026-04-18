import pandas as pd
import numpy as np
import sys
import os
sys.path.insert(0, "src")

print("Starting main.py...")  # add this line
sys.path.insert(0, "src")
print("Importing modules...")  # add this line

from data import VN30_CONSTITUENTS, VN30_RESERVES
from signals import compute_momentum
from portfolio_jt import build_jt_portfolios
from portfolio_monthly import build_portfolios, compute_benchmark
from performance import compute_metrics, print_summary_table, plot_comparison

# ── 1. Load prices ──────────────────────────────────────────────────────────────
print("="*60)
print("VN30 Momentum Strategy — Full Pipeline")
print("="*60)

print("\nStep 1: Loading prices...")
prices = pd.read_csv(
    "data/processed/prices.csv",
    index_col=0, parse_dates=True
)
print(f"  Shape : {prices.shape}")
print(f"  Period: {prices.index[0].date()} to {prices.index[-1].date()}")

# ── 2. Benchmark ────────────────────────────────────────────────────────────────
print("\nStep 2: Computing benchmark...")
benchmark = compute_benchmark(prices)
print(f"  Benchmark months: {len(benchmark)}")

# ── 3. Run all strategies ───────────────────────────────────────────────────────
print("\nStep 3: Running all strategies...")

all_metrics = {}
all_cums    = {}
all_dds     = {}

# Cache to avoid recomputing same formation period twice
portfolio_cache = {}

# JT overlapping strategies
jt_strategies = {
    "LS 3-1-6"  : (3,  1, 6, "ls"),
    "LO 3-1-6"  : (3,  1, 6, "lo"),
    "LS 6-1-6"  : (6,  1, 6, "ls"),
    "LO 6-1-6"  : (6,  1, 6, "lo"),
    "LS 12-1-6" : (12, 1, 6, "ls"),
    "LO 12-1-6" : (12, 1, 6, "lo"),
}

for name, (f, s, h, side) in jt_strategies.items():
    cache_key = (f, s, h)
    if cache_key not in portfolio_cache:
        print(f"  Building JT portfolio (formation={f})...")
        port = build_jt_portfolios(prices, formation=f, skip=s, holding=h)
        portfolio_cache[cache_key] = port
    else:
        port = portfolio_cache[cache_key]

    common = port.index.intersection(benchmark.index)
    col    = "long_short_return" if side == "ls" else "long_only_return"
    series = port.loc[common, col]

    m, cum, dd        = compute_metrics(series, name)
    all_metrics[name] = m
    all_cums[name]    = cum
    all_dds[name]     = dd

# Monthly rebalancing strategies
print("  Building monthly rebalancing portfolios...")
for f in [3, 12]:
    momentum = compute_momentum(prices, lookback=f, skip=1)
    port_m   = build_portfolios(prices, momentum)
    common   = port_m.index.intersection(benchmark.index)

    for side, col, label in [
        ("ls", "long_short_return", f"LS {f}-1 Monthly"),
        ("lo", "long_only_return",  f"LO {f}-1 Monthly"),
    ]:
        series             = port_m.loc[common, col]
        m, cum, dd         = compute_metrics(series, label)
        all_metrics[label] = m
        all_cums[label]    = cum
        all_dds[label]     = dd

# Benchmark
bm_common                    = benchmark.reindex(common)
m, cum, dd                   = compute_metrics(bm_common, "Benchmark")
all_metrics["Benchmark"]     = m
all_cums["Benchmark"]        = cum
all_dds["Benchmark"]         = dd

# ── 4. Print results ────────────────────────────────────────────────────────────
print("\nStep 4: Results")

# JT overlapping strategies
jt_results = {k: v for k, v in all_metrics.items()
              if "Monthly" not in k}
print("\nJT Overlapping Strategies:")
print_summary_table(jt_results)

# Monthly rebalancing strategies
monthly_results = {k: v for k, v in all_metrics.items()
                   if "Monthly" in k or k == "Benchmark"}
print("\nMonthly Rebalancing Strategies:")
print_summary_table(monthly_results)

# ── 5. Plot key strategies ──────────────────────────────────────────────────────
print("\nStep 5: Plotting...")
key_cum = {k: v for k, v in all_cums.items()
           if k in ["LS 3-1-6", "LO 3-1-6", "LO 12-1-6", "Benchmark"]}
key_dd  = {k: v for k, v in all_dds.items()
           if k in ["LS 3-1-6", "LO 3-1-6", "LO 12-1-6", "Benchmark"]}

plot_comparison(key_cum, key_dd, title="VN30 Momentum Strategy")

# ── 6. Save ─────────────────────────────────────────────────────────────────────
print("\nStep 6: Saving results...")
os.makedirs("output", exist_ok=True)
pd.DataFrame(all_metrics).to_csv("output/all_strategies.csv")
print("  Saved to output/all_strategies.csv")
print("\nDone!")
