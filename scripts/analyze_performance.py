#!/usr/bin/env python3
import argparse
import glob
import os
import re
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Optional, Tuple, Dict

try:
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

sns.set_context("talk")
sns.set_style("whitegrid")


def detect_time_unit(series: pd.Series) -> str:
    # Heuristic detection based on magnitude
    s = series.dropna().astype(float)
    if s.empty:
        return "s"
    v = float(s.iloc[0])
    # Rough thresholds
    if v > 1e17:
        return "ns"
    if v > 1e14:
        return "us"
    if v > 1e11:
        return "ms"
    if v > 1e9:
        return "s"  # seconds since epoch, high enough for UTC
    # Fallback by range
    if v > 1e12:
        return "ms"
    return "s"


def to_datetime(series: pd.Series, unit: Optional[str]) -> pd.Series:
    s = series.copy()
    if pd.api.types.is_datetime64_any_dtype(s):
        return pd.to_datetime(s, utc=True, errors="coerce")
    # Try numeric epoch units or ISO strings
    if unit == "auto" or unit is None:
        unit = detect_time_unit(s)
    # Try epoch numeric conversion; if fails, parse as string
    try:
        s_num = pd.to_numeric(s, errors="coerce")
        dt = pd.to_datetime(s_num, unit=unit, utc=True, errors="coerce")
        if dt.notna().sum() >= s.notna().sum() * 0.8:
            return dt
    except Exception:
        pass
    return pd.to_datetime(s, utc=True, errors="coerce")


def bootstrap_ci(data: np.ndarray, func, n_boot: int = 1000, ci: float = 0.95, random_state: int = 42) -> Tuple[float, float]:
    rng = np.random.default_rng(random_state)
    n = len(data)
    if n == 0:
        return (math.nan, math.nan)
    boots = np.empty(n_boot)
    for i in range(n_boot):
        sample = rng.choice(data, size=n, replace=True)
        boots[i] = func(sample)
    alpha = 1 - ci
    lower = np.quantile(boots, alpha / 2)
    upper = np.quantile(boots, 1 - alpha / 2)
    return lower, upper


def mean_ci_t(data: np.ndarray, ci: float = 0.95) -> Tuple[float, float]:
    n = len(data)
    if n <= 1 or np.isnan(data).all():
        return (math.nan, math.nan)
    mean = float(np.mean(data))
    sd = float(np.std(data, ddof=1))
    se = sd / math.sqrt(n)
    if SCIPY_AVAILABLE:
        tcrit = stats.t.ppf(1 - (1 - ci) / 2, df=n - 1)
    else:
        # normal approx if scipy not available
        tcrit = 1.96
    return (mean - tcrit * se, mean + tcrit * se)


def extract_load_from_name(path: str) -> Optional[int]:
    # Extract first integer like 1200 from filename
    m = re.search(r'(\d{2,6})', os.path.basename(path))
    return int(m.group(1)) if m else None


def load_csv(path: str,
             time_col: Optional[str],
             time_unit: Optional[str],
             latency_col: str,
             status_col: Optional[str]) -> pd.DataFrame:
    df = pd.read_csv(path)
    # Normalize column names for flexible matching
    cols = {c.lower(): c for c in df.columns}
    # Time
    if time_col is not None:
        tc = time_col
    else:
        # Try common defaults
        for cand in ["timestamp", "time", "ts", "datetime", "started_at"]:
            if cand in cols:
                tc = cols[cand]
                break
        else:
            tc = None
    if tc is not None:
        df["_dt"] = to_datetime(df[tc], unit=time_unit)
    else:
        df["_dt"] = pd.NaT

    # Latency
    if latency_col is None:
        for cand in ["latency_ms", "duration_ms", "http_req_duration", "latency", "response_time_ms"]:
            if cand in cols:
                latency_col = cols[cand]
                break
    if latency_col is None or latency_col not in df.columns:
        raise ValueError(f"Latency column not found. Provide --latency-col. Available: {list(df.columns)}")

    # Ensure milliseconds as float
    lat = pd.to_numeric(df[latency_col], errors="coerce")
    # Heuristic: if most latencies < 10, might be seconds — convert to ms
    if lat.notna().sum() > 0:
        m = lat.dropna().median()
        if m is not None and m < 10:
            # assume seconds -> ms
            lat = lat * 1000.0
    df["_lat_ms"] = lat

    # Status
    st = None
    if status_col is not None and status_col in df.columns:
        st = pd.to_numeric(df[status_col], errors="coerce")
    else:
        for cand in ["status", "status_code", "http_status", "code"]:
            if cand in cols:
                st = pd.to_numeric(df[cols[cand]], errors="coerce")
                break
    df["_status"] = st

    return df


def summarize_metrics(df: pd.DataFrame, label: str) -> Dict[str, float]:
    lat = df["_lat_ms"].dropna().to_numpy()
    n = len(lat)
    mean = float(np.mean(lat)) if n else math.nan
    std = float(np.std(lat, ddof=1)) if n > 1 else math.nan
    p50 = float(np.percentile(lat, 50)) if n else math.nan
    p90 = float(np.percentile(lat, 90)) if n else math.nan
    p95 = float(np.percentile(lat, 95)) if n else math.nan
    p99 = float(np.percentile(lat, 99)) if n else math.nan
    mean_lo, mean_hi = mean_ci_t(lat, ci=0.95)
    p95_lo, p95_hi = bootstrap_ci(lat, lambda x: np.percentile(x, 95), n_boot=1000, ci=0.95) if n else (math.nan, math.nan)
    p99_lo, p99_hi = bootstrap_ci(lat, lambda x: np.percentile(x, 99), n_boot=1000, ci=0.95) if n else (math.nan, math.nan)

    # Error rate (if status present)
    err_rate = math.nan
    if "_status" in df.columns and df["_status"].notna().any():
        ok = ((df["_status"] >= 200) & (df["_status"] < 400)).sum()
        err = ((df["_status"] < 200) | (df["_status"] >= 400)).sum()
        tot = ok + err
        err_rate = (err / tot) if tot > 0 else math.nan

    # Throughput overall (if time present)
    thr = math.nan
    if "_dt" in df.columns and df["_dt"].notna().any():
        dt = df["_dt"].sort_values()
        duration = (dt.iloc[-1] - dt.iloc[0]).total_seconds()
        if duration > 0:
            thr = n / duration

    return {
        "label": label,
        "samples": n,
        "mean_ms": mean,
        "mean_ci95_lo": mean_lo,
        "mean_ci95_hi": mean_hi,
        "std_ms": std,
        "p50_ms": p50,
        "p90_ms": p90,
        "p95_ms": p95,
        "p95_ci95_lo": p95_lo,
        "p95_ci95_hi": p95_hi,
        "p99_ms": p99,
        "p99_ci95_lo": p99_lo,
        "p99_ci95_hi": p99_hi,
        "error_rate": err_rate,
        "throughput_rps": thr,
    }


def per_second_series(df: pd.DataFrame) -> Tuple[pd.Series, pd.DataFrame]:
    if "_dt" not in df.columns or df["_dt"].notna().sum() == 0:
        return pd.Series(dtype=float), pd.DataFrame()
    d = df.dropna(subset=["_dt"]).set_index("_dt").sort_index()
    # Throughput per second
    thr = d["_lat_ms"].resample("1S").size().rename("rps")
    # Rolling/tumbling latency percentiles per 1s
    # Use groupby resample to compute quantiles
    qdf = d["_lat_ms"].resample("1S").quantile([0.5, 0.9, 0.95, 0.99]).unstack().rename(columns={
        0.5: "p50_ms", 0.9: "p90_ms", 0.95: "p95_ms", 0.99: "p99_ms"
    })
    return thr, qdf


def plot_latency_cdf(lat: np.ndarray, out_path: str, title: str):
    if len(lat) == 0:
        return
    plt.figure(figsize=(8,6))
    x = np.sort(lat)
    y = np.linspace(0, 1, len(x))
    plt.plot(x, y, label="CDF")
    plt.xlabel("Latency (ms)")
    plt.ylabel("Probability")
    plt.title(title)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def plot_timeseries(thr: pd.Series, qdf: pd.DataFrame, out_prefix: str, label: str):
    if not thr.empty:
        plt.figure(figsize=(10,5))
        thr.plot(color="tab:blue")
        plt.title(f"Throughput over time (RPS) - {label}")
        plt.xlabel("Time (s)")
        plt.ylabel("Requests/sec")
        plt.tight_layout()
        plt.savefig(f"{out_prefix}_throughput_ts.png", dpi=150)
        plt.close()

    if not qdf.empty:
        plt.figure(figsize=(10,6))
        for col, color in zip(["p50_ms", "p90_ms", "p95_ms", "p99_ms"],
                              ["tab:green", "tab:orange", "tab:red", "tab:purple"]):
            if col in qdf.columns:
                plt.plot(qdf.index, qdf[col], label=col.replace("_", " ").upper(), color=color, alpha=0.9)
        plt.title(f"Latency percentiles over time - {label}")
        plt.xlabel("Time")
        plt.ylabel("Latency (ms)")
        plt.legend()
        plt.tight_layout()
        plt.savefig(f"{out_prefix}_latency_ts.png", dpi=150)
        plt.close()


def aggregate_plot_tail_vs_load(summaries: pd.DataFrame, out_path: str, title: str):
    if "load" not in summaries.columns:
        return
    plt.figure(figsize=(8,6))
    for pct_col, color in [("p95_ms", "tab:red"), ("p99_ms", "tab:purple")]:
        if pct_col in summaries.columns:
            plt.plot(summaries["load"], summaries[pct_col], marker="o", label=pct_col.upper(), color=color)
    plt.xlabel("Offered load (transactions)")
    plt.ylabel("Latency (ms)")
    plt.title(title)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def aggregate_plot_throughput_vs_load(summaries: pd.DataFrame, out_path: str, title: str):
    if "load" not in summaries.columns or "throughput_rps" not in summaries.columns:
        return
    plt.figure(figsize=(8,6))
    plt.plot(summaries["load"], summaries["throughput_rps"], marker="o", color="tab:blue")
    plt.xlabel("Offered load (transactions)")
    plt.ylabel("Throughput (RPS)")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def main():
    ap = argparse.ArgumentParser(description="Analyze performance CSVs for Fincube and produce metrics and plots.")
    ap.add_argument("--input-dir", required=True, help="Directory with CSVs for Fincube distributed system.")
    ap.add_argument("--baseline-dir", default=None, help="Optional directory with baseline CSVs (e.g., monolith/REST).")
    ap.add_argument("--output-dir", default="reports", help="Directory to write reports and figures.")
    ap.add_argument("--time-col", default=None, help="Name of timestamp column (default: auto-detect).")
    ap.add_argument("--time-unit", default="auto", choices=["auto", "ns", "us", "ms", "s"], help="Epoch unit for time column.")
    ap.add_argument("--latency-col", default=None, help="Latency column name (ms or s; auto converts to ms).")
    ap.add_argument("--status-col", default=None, help="HTTP status column name (for error rate).")
    ap.add_argument("--pattern", default="*.csv", help="Glob pattern to read CSVs in input directories.")
    args = ap.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    fig_dir = os.path.join(args.output_dir, "figures")
    os.makedirs(fig_dir, exist_ok=True)

    def process_dir(dpath: str, tag: str):
        paths = sorted(glob.glob(os.path.join(dpath, args.pattern)))
        summaries = []
        for p in paths:
            try:
                df = load_csv(p, args.time_col, args.time_unit, args.latency_col, args.status_col)
            except Exception as e:
                print(f"[WARN] Skipping {p}: {e}")
                continue
            load_val = extract_load_from_name(p)
            label = f"{tag}-{load_val}" if load_val else f"{tag}-{os.path.basename(p)}"
            met = summarize_metrics(df, label=label)
            met["file"] = p
            met["tag"] = tag
            met["load"] = load_val
            summaries.append(met)

            # CDF plot
            lat = df["_lat_ms"].dropna().to_numpy()
            cdf_path = os.path.join(fig_dir, f"{tag}_{load_val}_latency_cdf.png" if load_val else f"{tag}_{os.path.basename(p)}_latency_cdf.png")
            plot_latency_cdf(lat, cdf_path, f"Latency CDF - {label}")

            # Timeseries plots
            thr_s, qdf = per_second_series(df)
            out_prefix = os.path.join(fig_dir, f"{tag}_{load_val}" if load_val else f"{tag}_{os.path.basename(p)}")
            plot_timeseries(thr_s, qdf, out_prefix, label=label)

        if summaries:
            df_sum = pd.DataFrame(summaries).sort_values(by=["load", "file"], na_position="last")
            df_sum.to_csv(os.path.join(args.output_dir, f"summary_{tag}.csv"), index=False)
            return df_sum
        return pd.DataFrame()

    fin_df = process_dir(args.input_dir, tag="fincube")
    base_df = pd.DataFrame()
    if args.baseline_dir:
        base_df = process_dir(args.baseline_dir, tag="baseline")

    # Aggregate comparative plots by load if both present
    if not fin_df.empty:
        aggregate_plot_tail_vs_load(
            fin_df.dropna(subset=["load"]),
            os.path.join(fig_dir, "fincube_tail_latency_vs_load.png"),
            "Fincube Tail Latency vs Offered Load"
        )
        aggregate_plot_throughput_vs_load(
            fin_df.dropna(subset=["load"]),
            os.path.join(fig_dir, "fincube_throughput_vs_load.png"),
            "Fincube Throughput vs Offered Load"
        )

    if not fin_df.empty and not base_df.empty:
        # Merge on load for side-by-side comparison
        merged = pd.merge(
            fin_df.dropna(subset=["load"])[["load", "p95_ms", "p99_ms", "throughput_rps"]].rename(
                columns={"p95_ms": "fincube_p95_ms", "p99_ms": "fincube_p99_ms", "throughput_rps": "fincube_rps"}),
            base_df.dropna(subset=["load"])[["load", "p95_ms", "p99_ms", "throughput_rps"]].rename(
                columns={"p95_ms": "baseline_p95_ms", "p99_ms": "baseline_p99_ms", "throughput_rps": "baseline_rps"}),
            on="load", how="inner"
        )
        comp_path = os.path.join(args.output_dir, "summary_comparison.csv")
        merged.to_csv(comp_path, index=False)

        # Plot comparative tail latency
        if not merged.empty:
            plt.figure(figsize=(8,6))
            plt.plot(merged["load"], merged["fincube_p95_ms"], marker="o", label="Fincube p95", color="tab:red")
            plt.plot(merged["load"], merged["baseline_p95_ms"], marker="o", label="Baseline p95", color="tab:pink")
            plt.plot(merged["load"], merged["fincube_p99_ms"], marker="o", label="Fincube p99", color="tab:purple")
            plt.plot(merged["load"], merged["baseline_p99_ms"], marker="o", label="Baseline p99", color="mediumpurple")
            plt.xlabel("Offered load (transactions)")
            plt.ylabel("Latency (ms)")
            plt.title("Tail latency vs load: Fincube vs Baseline")
            plt.legend()
            plt.tight_layout()
            plt.savefig(os.path.join(fig_dir, "compare_tail_latency_vs_load.png"), dpi=150)
            plt.close()

            # Throughput comparison
            plt.figure(figsize=(8,6))
            plt.plot(merged["load"], merged["fincube_rps"], marker="o", label="Fincube RPS", color="tab:blue")
            plt.plot(merged["load"], merged["baseline_rps"], marker="o", label="Baseline RPS", color="tab:cyan")
            plt.xlabel("Offered load (transactions)")
            plt.ylabel("Throughput (RPS)")
            plt.title("Throughput vs load: Fincube vs Baseline")
            plt.legend()
            plt.tight_layout()
            plt.savefig(os.path.join(fig_dir, "compare_throughput_vs_load.png"), dpi=150)
            plt.close()

    print(f"Done. Reports in: {args.output_dir} and figures in: {fig_dir}")


if __name__ == "__main__":
    main()