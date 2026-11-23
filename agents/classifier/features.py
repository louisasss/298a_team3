import numpy as np
import pandas as pd

from simulate import ROUTES

FEATURES = [
    "error_rate_diff", "p95_ratio", "p50_ratio",
    "canary_requests", "stable_requests", "canary_weight", "minutes_since_start",
    "d_error_rate_diff", "d_p95_ratio", "d_p50_ratio", "worst_route_error_diff",
]

def main():
    raw = pd.read_csv("agents/classifier/data/raw_windows.csv")
    canary = raw[raw.version == "canary"]
    stable = raw[raw.version == "stable"]
    df = canary.merge(stable, on=["run_id", "window"], suffixes=("_c", "_s"))

    df["error_rate_diff"] = df.errors_c / df.requests_c - df.errors_s / df.requests_s
    df["p95_ratio"] = df.p95_ms_c / df.p95_ms_s
    df["p50_ratio"] = df.p50_ms_c / df.p50_ms_s
    df["canary_requests"] = df.requests_c
    df["stable_requests"] = df.requests_s
    df["canary_weight"] = df.weight_c
    df["minutes_since_start"] = df.window

    df = df.sort_values(["run_id", "window"])
    df["d_error_rate_diff"] = df.groupby("run_id")["error_rate_diff"].diff().fillna(0)
    df["d_p95_ratio"] = df.groupby("run_id")["p95_ratio"].diff().fillna(0)
    df["d_p50_ratio"] = df.groupby("run_id")["p50_ratio"].diff().fillna(0)

    diffs = []
    for route in ROUTES:
        rc, ec = df[f"req::{route}_c"], df[f"err::{route}_c"]
        rs, es = df[f"req::{route}_s"], df[f"err::{route}_s"]
        d = ec / rc - es / rs
        diffs.append(d.where((rc >= 10) & (rs >= 10)))   # too few requests → missing
    df["worst_route_error_diff"] = pd.concat(diffs, axis=1).max(axis=1)

    df = df[(df.requests_c > 0) & (df.requests_s > 0)]
    df = df.dropna(subset=["label_c"])
    df = df.rename(columns={"label_c": "label"})
    df["label"] = df["label"].astype(int)

    pd.DataFrame(df[["run_id", "window"] + FEATURES + ["label"]]).to_csv("agents/classifier/data/features.csv", index=False)
    print(f"{len(df)} windows written")


if __name__ == "__main__":
    main()