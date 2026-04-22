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
def compute_rolling_sharpe(returns, window=12, rf=0.0, freq=12):
    """
    Compute rolling annualised Sharpe ratio.

    Parameters
    ----------
    returns : Series of monthly returns
    window  : rolling window in periods (default 12 = 1 year of monthly data)
    rf      : annual risk-free rate (default 0)
    freq    : periods per year (default 12 for monthly)
    """
    rf_per_period  = rf / freq
    rolling_mean   = returns.rolling(window).mean()
    rolling_std    = returns.rolling(window).std()
    rolling_sharpe = ((rolling_mean - rf_per_period) * freq) / (rolling_std * np.sqrt(freq))
    rolling_sharpe.name = f"Rolling_Sharpe_{window}m"
    return rolling_sharpe


def plot_rolling_sharpe(strategies_returns, window=12,
                        title="VN30 Monthly Momentum"):
    """
    Plot rolling Sharpe ratio for multiple strategies.

    Parameters
    ----------
    strategies_returns : dict of {name: return_series}
    window             : rolling window in months (default 12 = 1 year)
    """
    colors = {
        "LS Monthly"    : "steelblue",
        "LO Monthly"    : "darkorange",
        "LS JT (12-1-6)": "green",
        "LO JT (12-1-6)": "red",
        "Benchmark"     : "grey",
    }

    fig, axes = plt.subplots(2, 1, figsize=(13, 9))
    fig.suptitle(f"{title} — Rolling {window}-Month Sharpe Ratio",
                 fontsize=13, fontweight="bold")

    # Panel 1: Rolling Sharpe all strategies
    ax = axes[0]
    for name, ret in strategies_returns.items():
        rs = compute_rolling_sharpe(ret.dropna(), window=window)
        ax.plot(rs.index, rs.values, label=name,
                color=colors.get(name, "black"), linewidth=1.5)

    ax.axhline(y=0, color="black", linestyle="-", linewidth=0.8)
    ax.axhline(y=1, color="green", linestyle=":", linewidth=1.0,
               alpha=0.7, label="Sharpe = 1")
    ax.axhline(y=-1, color="red", linestyle=":", linewidth=1.0, alpha=0.7)
    ax.set_ylabel("Rolling Sharpe Ratio")
    ax.set_title(f"Rolling {window}-Month Sharpe (annualised)")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(alpha=0.3)
    ax.set_ylim(-4, 5)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    # Panel 2: Bar chart for first strategy
    ax = axes[1]
    first_name = list(strategies_returns.keys())[0]
    rs_main    = compute_rolling_sharpe(
        strategies_returns[first_name].dropna(), window=window
    ).dropna()
    bar_colors = ["steelblue" if v >= 0 else "red" for v in rs_main.values]
    ax.bar(rs_main.index, rs_main.values, color=bar_colors,
           alpha=0.6, width=15)
    ax.axhline(y=0, color="black", linewidth=0.8)
    pct_pos = (rs_main >= 0).mean() * 100
    ax.set_ylabel("Sharpe Ratio")
    ax.set_title(
        f"{first_name} — {pct_pos:.0f}% of months with positive rolling Sharpe"
    )
    ax.grid(alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    plt.tight_layout()
    os.makedirs("output", exist_ok=True)
    plt.savefig("output/rolling_sharpe.png", dpi=150, bbox_inches="tight")
    plt.show()
    print("Saved to output/rolling_sharpe.png")


def print_sharpe_regime_summary(strategies_returns, window=12):
    """
    Print Sharpe regime statistics across strategies.
    """
    print(f"\n{'='*65}")
    print(f"  ROLLING SHARPE REGIME ANALYSIS ({window}-month window)")
    print(f"{'='*65}")
    print(f"  {'Strategy':<25} {'Mean':>8} {'Std':>8} "
          f"{'% Positive':>12} {'Min':>8} {'Max':>8}")
    print(f"  {'─'*60}")
    for name, ret in strategies_returns.items():
        rs = compute_rolling_sharpe(ret.dropna(), window=window).dropna()
        print(f"  {name:<25} {rs.mean():>8.2f} {rs.std():>8.2f} "
              f"{(rs>=0).mean()*100:>11.1f}% "
              f"{rs.min():>8.2f} {rs.max():>8.2f}")
    print(f"{'='*65}")
    
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
        "LS 3-1-6"  : "steelblue",
        "LO 3-1-6"  : "darkorange",
        "LS 6-1-6"  : "green",
        "LO 6-1-6"  : "red",
        "LS 12-1-6" : "purple",
        "LO 12-1-6" : "brown",
        "Benchmark" : "grey",
    }
    linestyles = {
        "LS 3-1-6"  : "-",
        "LO 3-1-6"  : "-",
        "LS 6-1-6"  : "--",
        "LO 6-1-6"  : "--",
        "LS 12-1-6" : "-.",
        "LO 12-1-6" : "-.",
        "Benchmark" : ":",
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

