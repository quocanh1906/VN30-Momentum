import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os

def compute_metrics(returns, name="Strategy", rf=0.0):
    """
    Compute standard performance metrics for a return series.

    Parameters
    ----------
    returns : Series of monthly returns
    name    : label for printing
    rf      : annual risk-free rate (default 0)
    """
    r = returns.dropna()

    ann_return  = r.mean() * 12
    ann_vol     = r.std() * np.sqrt(12)
    sharpe      = (ann_return - rf) / ann_vol if ann_vol > 0 else np.nan

    # Drawdown
    cum         = (1 + r).cumprod()
    rolling_max = cum.cummax()
    drawdown    = (cum - rolling_max) / rolling_max
    max_dd      = drawdown.min()

    # Win rate
    win_rate = (r > 0).mean()

    # Best/worst month
    best_month  = r.max()
    worst_month = r.min()

    metrics = {
        "Ann. Return (%)"   : round(ann_return * 100, 2),
        "Ann. Volatility (%)": round(ann_vol * 100, 2),
        "Sharpe Ratio"      : round(sharpe, 3),
        "Max Drawdown (%)"  : round(max_dd * 100, 2),
        "Win Rate (%)"      : round(win_rate * 100, 2),
        "Best Month (%)"    : round(best_month * 100, 2),
        "Worst Month (%)"   : round(worst_month * 100, 2),
        "N Months"          : len(r),
    }

    print(f"\n{'='*40}")
    print(f"  {name}")
    print(f"{'='*40}")
    for k, v in metrics.items():
        print(f"  {k:<22}: {v}")

    return metrics, cum, drawdown

def plot_results(portfolios, benchmark):
    """
    Plot cumulative returns and drawdowns for all strategies.
    """
    ls  = portfolios["long_short_return"].dropna()
    lo  = portfolios["long_only_return"].dropna()
    bm  = benchmark.dropna()

    # Align all series
    common = ls.index.intersection(lo.index).intersection(bm.index)
    ls  = ls.loc[common]
    lo  = lo.loc[common]
    bm  = bm.loc[common]

    ls_cum = (1 + ls).cumprod()
    lo_cum = (1 + lo).cumprod()
    bm_cum = (1 + bm).cumprod()

    ls_dd  = (ls_cum - ls_cum.cummax()) / ls_cum.cummax()
    lo_dd  = (lo_cum - lo_cum.cummax()) / lo_cum.cummax()
    bm_dd  = (bm_cum - bm_cum.cummax()) / bm_cum.cummax()

    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    fig.suptitle("VN30 Momentum Strategy — Performance (2018–2024)",
                 fontsize=13, fontweight="bold")

    # Cumulative returns
    axes[0].plot(ls_cum.index, ls_cum.values,
                 label="Long-Short", color="steelblue", linewidth=1.8)
    axes[0].plot(lo_cum.index, lo_cum.values,
                 label="Long-Only", color="darkorange", linewidth=1.8)
    axes[0].plot(bm_cum.index, bm_cum.values,
                 label="VN30 Benchmark", color="grey",
                 linewidth=1.2, linestyle="--")
    axes[0].axhline(y=1, color="black", linestyle=":", linewidth=0.8)
    axes[0].set_ylabel("Cumulative Return (VND 1 invested)")
    axes[0].legend(loc="upper left")
    axes[0].grid(alpha=0.3)
    axes[0].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    # Drawdowns
    axes[1].fill_between(ls_dd.index, ls_dd.values * 100, 0,
                          label="Long-Short", color="steelblue", alpha=0.4)
    axes[1].fill_between(lo_dd.index, lo_dd.values * 100, 0,
                          label="Long-Only", color="darkorange", alpha=0.4)
    axes[1].fill_between(bm_dd.index, bm_dd.values * 100, 0,
                          label="VN30 Benchmark", color="grey", alpha=0.25)
    axes[1].set_ylabel("Drawdown (%)")
    axes[1].legend(loc="lower left")
    axes[1].grid(alpha=0.3)
    axes[1].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    plt.tight_layout()
    os.makedirs("output", exist_ok=True)
    plt.savefig("output/performance.png", dpi=150, bbox_inches="tight")
    plt.show()
    print("\nChart saved to output/performance.png")

def print_summary_table(ls_metrics, lo_metrics, bm_metrics):
    """Print a clean comparison table."""
    print(f"\n{'='*60}")
    print(f"{'Metric':<25} {'Long-Short':>12} {'Long-Only':>12} {'Benchmark':>12}")
    print(f"{'='*60}")
    for key in ls_metrics:
        print(f"{key:<25} {str(ls_metrics[key]):>12} "
              f"{str(lo_metrics[key]):>12} {str(bm_metrics[key]):>12}")
    print(f"{'='*60}")

if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")

    # Load data
    portfolios = pd.read_csv(
        "data/processed/portfolios.csv",
        index_col=0, parse_dates=True
    )
    benchmark = pd.read_csv(
        "data/processed/benchmark.csv",
        index_col=0, parse_dates=True
    ).squeeze()

    print(f"Portfolio period: {portfolios.index[0].date()} "
          f"to {portfolios.index[-1].date()}")
    print(f"Months: {len(portfolios)}")

    # Compute metrics
    ls_metrics, ls_cum, ls_dd = compute_metrics(
        portfolios["long_short_return"], "Long-Short Momentum"
    )
    lo_metrics, lo_cum, lo_dd = compute_metrics(
        portfolios["long_only_return"], "Long-Only Momentum"
    )
    bm_metrics, bm_cum, bm_dd = compute_metrics(
        benchmark, "VN30 Equal-Weight Benchmark"
    )

    # Summary table
    print_summary_table(ls_metrics, lo_metrics, bm_metrics)

    # Plot
    plot_results(portfolios, benchmark)

    # Save metrics
    summary = pd.DataFrame({
        "Long-Short" : ls_metrics,
        "Long-Only"  : lo_metrics,
        "Benchmark"  : bm_metrics,
    })
    summary.to_csv("output/metrics.csv")
    print("Metrics saved to output/metrics.csv")