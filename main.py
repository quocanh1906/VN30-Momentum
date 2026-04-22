import pandas as pd
import numpy as np
import sys
import os
sys.path.insert(0, "src")

from data import download_etf_benchmark
from portfolio import build_portfolios, compute_benchmark
from performance import (compute_metrics, print_summary_table, plot_comparison,
                         compute_rolling_sharpe, plot_rolling_sharpe,
                         print_sharpe_regime_summary)

print("=" * 60)
print("VN30 Momentum Strategy — Full Pipeline")
print("=" * 60)

# ── 1. Load prices ──────────────────────────────────────────────────────────────
print("\nStep 1: Loading prices...")
prices = pd.read_csv(
    "data/processed/prices.csv",
    index_col=0, parse_dates=True
)
print(f"  Shape : {prices.shape}")
print(f"  Period: {prices.index[0].date()} to {prices.index[-1].date()}")

# ── 2. Benchmark ────────────────────────────────────────────────────────────────
print("\nStep 2: Loading ETF benchmark...")
benchmark = download_etf_benchmark(
    symbol="E1VFVN30",
    start ="2015-01-01",
    end   ="2024-12-31"
)
if benchmark is None:
    print("  ETF download failed — falling back to equal-weighted benchmark")
    benchmark = compute_benchmark(prices)

# Force month-end alignment
benchmark.index = pd.to_datetime(benchmark.index) + pd.offsets.MonthEnd(0)
print(f"  Months : {len(benchmark)}")

# ── 3. Run strategies ───────────────────────────────────────────────────────────
print("\nStep 3: Running strategies...")

all_metrics = {}
all_cums    = {}
all_dds     = {}
all_returns = {}
port_cache  = {}

def run_strategy(name, formation, skip, holding, col, cost, prices, benchmark):
    """Build portfolio, align to benchmark, compute metrics."""
    cache_key = (formation, skip, holding, cost)
    if cache_key not in port_cache:
        print(f"  Building {formation}-{skip}-{holding} "
              f"(cost={cost*100:.3f}%)...")
        port_cache[cache_key] = build_portfolios(
            prices, formation=formation, skip=skip,
            holding=holding, cost_per_trade=cost
        )
    port = port_cache[cache_key].copy()

    # Align index to month-end
    port.index = pd.to_datetime(port.index) + pd.offsets.MonthEnd(0)
    common     = port.index.intersection(benchmark.index)
    series     = port.loc[common, col]

    return series

# Formation period comparison — no costs
formations = [
    ("LS 3-1-6",  3,  1, 6, "long_short_return", 0.0),
    ("LO 3-1-6",  3,  1, 6, "long_only_return",  0.0),
    ("LS 6-1-6",  6,  1, 6, "long_short_return", 0.0),
    ("LO 6-1-6",  6,  1, 6, "long_only_return",  0.0),
    ("LS 12-1-6", 12, 1, 6, "long_short_return", 0.0),
    ("LO 12-1-6", 12, 1, 6, "long_only_return",  0.0),
]

for name, f, s, h, col, cost in formations:
    series             = run_strategy(name, f, s, h, col, cost, prices, benchmark)
    m, cum, dd         = compute_metrics(series, name)
    all_metrics[name]  = m
    all_cums[name]     = cum
    all_dds[name]      = dd
    all_returns[name]  = series

# Transaction cost sensitivity — best formation LS 3-1-6
print("\n  Transaction cost sensitivity (3-1-6 LS)...")
cost_scenarios = [
    ("LS (no cost)",     3, 1, 6, "long_short_return", 0.000),
    ("LS (Realistic)",   3, 1, 6, "long_short_return", 0.00125),
    ("LS (Conservative)",3, 1, 6, "long_short_return", 0.00175),
]
for name, f, s, h, col, cost in cost_scenarios:
    series             = run_strategy(name, f, s, h, col, cost, prices, benchmark)
    m, cum, dd         = compute_metrics(series, name)
    all_metrics[name]  = m
    all_cums[name]     = cum
    all_dds[name]      = dd
    all_returns[name]  = series

# Benchmark
bm_common                = benchmark.reindex(
    list(all_returns.values())[0].index
)
m, cum, dd               = compute_metrics(bm_common, "Benchmark")
all_metrics["Benchmark"] = m
all_cums["Benchmark"]    = cum
all_dds["Benchmark"]     = dd
all_returns["Benchmark"] = bm_common

# ── 4. Print results ────────────────────────────────────────────────────────────
print("\nStep 4: Results")

formation_results = {k: v for k, v in all_metrics.items()
                     if "-1-6" in k or k == "Benchmark"}
print("\nFormation Period Comparison:")
print_summary_table(formation_results)

cost_results = {k: v for k, v in all_metrics.items()
                if any(s in k for s in ["no cost", "Realistic", "Conservative"])
                or k == "Benchmark"}
print("\nTransaction Cost Sensitivity (3-1-6 LS):")
print_summary_table(cost_results)

# ── 5. Rolling Sharpe ───────────────────────────────────────────────────────────
print("\nStep 5: Rolling Sharpe analysis...")
rolling_strategies = {
    "LS 3-1-6" : all_returns["LS 3-1-6"],
    "LO 3-1-6" : all_returns["LO 3-1-6"],
    "LS 12-1-6": all_returns["LS 12-1-6"],
    "Benchmark" : all_returns["Benchmark"],
}
print_sharpe_regime_summary(rolling_strategies, window=12)

# ── 6. Plots ────────────────────────────────────────────────────────────────────
print("\nStep 6: Plotting...")
os.makedirs("output", exist_ok=True)

# Plot 1: formation comparison
key_cum = {k: v for k, v in all_cums.items()
           if k in ["LS 3-1-6", "LO 3-1-6", "LO 12-1-6", "Benchmark"]}
key_dd  = {k: v for k, v in all_dds.items()
           if k in ["LS 3-1-6", "LO 3-1-6", "LO 12-1-6", "Benchmark"]}
plot_comparison(key_cum, key_dd, title="VN30 Momentum Strategy")

# Plot 2: transaction cost impact
cost_cum = {k: v for k, v in all_cums.items()
            if any(s in k for s in ["no cost", "Realistic", "Conservative"])
            or k == "Benchmark"}
cost_dd  = {k: v for k, v in all_dds.items()
            if any(s in k for s in ["no cost", "Realistic", "Conservative"])
            or k == "Benchmark"}
plot_comparison(cost_cum, cost_dd,
                title="VN30 Momentum — Transaction Cost Impact")

# Plot 3: rolling Sharpe
plot_rolling_sharpe(rolling_strategies, window=12)

# ── 7. Save ─────────────────────────────────────────────────────────────────────
print("\nStep 7: Saving...")
pd.DataFrame(all_metrics).to_csv("output/all_strategies.csv")
print("  Saved to output/all_strategies.csv")
print("\nDone!")