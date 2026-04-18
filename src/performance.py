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

    cum         = (1 + r).cumprod()
    rolling_max = cum.cummax()
    drawdown    = (cum - rolling_max) / rolling_max
    max_dd      = drawdown.min()

    win_rate    = (r > 0).mean()
    best_month  = r.max()
    worst_month = r.min()

    metrics = {
        "Ann. Return (%)"    : round(ann_return * 100, 2),
        "Ann. Volatility (%)": round(ann_vol * 100, 2),
        "Sharpe Ratio"       : round(sharpe, 3),
        "Max Drawdown (%)"   : round(max_dd * 100, 2),
        "Win Rate (%)"       : round(win_rate * 100, 2),
        "Best Month (%)"     : round(best_month * 100, 2),
        "Worst Month (%)"    : round(worst_month * 100, 2),
        "N Months"           : len(r),
    }

    return metrics, cum, drawdown

def print_summary_table(strategies):
    """
    Print comparison table for multiple strategies.

    Parameters
    ----------
    strategies : dict of {name: metrics_dict}
    """
    names   = list(strategies.keys())
    metrics = list(strategies.values())
    keys    = list(metrics[0].keys())

    # Header
    print(f"\n{'='*80}")
    header = f"{'Metric':<25}"
    for name in names:
        header += f"{name:>17}"
    print(header)
    print(f"{'='*80}")

    # Rows
    for key in keys:
        row = f"{key:<25}"
        for m in metrics:
            row += f"{str(m[key]):>17}"
        print(row)
    print(f"{'='*80}")

def plot_comparison(strategies_cum, strategies_dd, title="VN30 Momentum Strategy"):
    """
    Plot cumulative returns and drawdowns for multiple strategies.

    Parameters
    ----------
    strategies_cum : dict of {name: cumulative return Series}
    strategies_dd  : dict of {name: drawdown Series}
    """
    colors = {
        "LS Monthly"   : "steelblue",
        "LO Monthly"   : "darkorange",
        "LS JT (12-1-6)": "green",
        "LO JT (12-1-6)": "red",
        "Benchmark"    : "grey",
    }
    linestyles = {
        "LS Monthly"   : "-",
        "LO Monthly"   : "-",
        "LS JT (12-1-6)": "--",
        "LO JT (12-1-6)": "--",
        "Benchmark"    : ":",
    }

    fig, axes = plt.subplots(2, 1, figsize=(13, 9))
    fig.suptitle(f"{title} — Performance (2018–2024)",
                 fontsize=13, fontweight="bold")

    for name, cum in strategies_cum.items():
        axes[0].plot(
            cum.index, cum.values,
            label=name,
            color=colors.get(name, "black"),
            linestyle=linestyles.get(name, "-"),
            linewidth=1.8
        )

    axes[0].axhline(y=1, color="black", linestyle=":", linewidth=0.8)
    axes[0].set_ylabel("Cumulative Return (VND 1 invested)")
    axes[0].legend(loc="upper left", fontsize=9)
    axes[0].grid(alpha=0.3)
    axes[0].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    for name, dd in strategies_dd.items():
        axes[1].fill_between(
            dd.index, dd.values * 100, 0,
            label=name,
            color=colors.get(name, "black"),
            alpha=0.25
        )

    axes[1].set_ylabel("Drawdown (%)")
    axes[1].legend(loc="lower left", fontsize=9)
    axes[1].grid(alpha=0.3)
    axes[1].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    plt.tight_layout()
    os.makedirs("output", exist_ok=True)
    plt.savefig("output/performance_comparison.png", dpi=150,
                bbox_inches="tight")
    plt.show()
    print("\nChart saved to output/performance_comparison.png")

