import numpy as np
import pandas as pd
import os

STEPS = [10, 25, 50, 100]          # Sang Ah's canary weights (%)
WINDOWS_PER_STEP = 2               # 2 one-minute windows per step → 8 windows per run
ROUTES = {                         # ParcelPost routes and their share of traffic
    "POST /shipments": 0.3,
    "GET /shipments/{shipment_id}": 0.5,
    "PATCH /shipments/{shipment_id}/status": 0.2,
}
TOTAL_RPM = 3000                   # requests per minute, before ±30% noise
BASE_ERROR = 0.005
BASE_P50, BASE_P95 = 80, 200       # ms
WARMUP_FACTOR = 1.3

# (latency multiplier, latency added in ms, extra error rate)
FAULTS = {
    "latency": {"low": (1.0, 20, 0.0), "medium": (1.0, 100, 0.0), "high": (1.0, 300, 0.0)},
    "error_spike": {"low": (1.0, 0, (0.01-BASE_ERROR)), "medium": (1.0, 0, (0.04-BASE_ERROR)), "high": (1.0, 0, (0.15-BASE_ERROR))},
    "cpu_stress": {"low": (1.1, 0, 0.002), "medium": (1.5, 0, .01), "high": (2.5, 0, 0.03)},
}
BAD_CONFIG_STRENGTH = {"low": 0.3, "medium": 1.0, "high": 3.0}

def fault_effect(fault, severity, weight):
    """Return (latency multiplier, latency added ms, extra error rate) for the canary."""
    if fault == "bad_config":
        s = BAD_CONFIG_STRENGTH[severity] * weight / 100
        multiplier = 1 + s
        error_effect = 0.01 * s
        return (multiplier, 0, error_effect)
    return FAULTS[fault][severity]

def simulate_window(rng, n_requests, effect, warmup):
    mult, add_ms, extra_err = effect
    row = {"requests": 0, "errors": 0}
    for route, share in ROUTES.items():
        req = rng.poisson(n_requests * share)
        err = rng.binomial(req, min(1.0, BASE_ERROR + extra_err))
        row[f"req::{route}"] = req
        row[f"err::{route}"] = err
        row["requests"] += req
        row["errors"] += err
    jitter = rng.normal(1.0, 0.10)      #   apply ±10% jitter:  * rng.normal(1.0, 0.10)
    p50 = BASE_P50 * jitter
    p95 = BASE_P95 * jitter
    if warmup:                          #   apply warm-up:      * WARMUP_FACTOR if warmup
        p50 = p50 * WARMUP_FACTOR
        p95 = p95 * WARMUP_FACTOR
    p50 = p50 * mult + add_ms           #   apply the fault:    * mult + add_ms
    p95 = p95 * mult + add_ms
    row["p50_ms"] = p50                 #   save row
    row["p95_ms"] = p95
    return row

def simulate_run(run_id, fault, severity, onset, run_class, seed):
    """fault=None for healthy runs. run_class: 'bad', 'harmless', 'borderline' or 'healthy'."""
    rng = np.random.default_rng(seed)
    onset_idx = 0 if onset == "start" else (len(STEPS) * WINDOWS_PER_STEP) // 2
    rows = []
    i = 0
    for weight in STEPS:
        for _ in range(WINDOWS_PER_STEP):
            total = TOTAL_RPM * rng.uniform(0.7, 1.3)              # ±30% traffic noise
            faulty_now = fault is not None and i >= onset_idx
            canary_effect = fault_effect(fault, severity, weight) if faulty_now else (1.0, 0, 0.0)

            canary = simulate_window(rng, total * weight / 100, canary_effect, warmup=(i == 0))
            stable = simulate_window(rng, total * (1 - weight / 100), (1.0, 0, 0.0), warmup=False)

            if run_class in ("bad", "borderline") and i > onset_idx:
                label = 1
            elif fault is not None and i == onset_idx:
                label = None
            else:
                label = 0
            for version, data in (("canary", canary), ("stable", stable)):
                rows.append({"run_id": run_id, "window": i, "weight": weight,
                             "version": version, "label": label, **data})
            i += 1
    return rows


HARMLESS = {("latency", "low"), ("cpu_stress", "low"), ("bad_config", "low")}
BORDERLINE = {("error_spike", "low")}

def run_class_for(fault, severity):
    if (fault, severity) in HARMLESS:
        return "harmless"
    elif (fault, severity) in BORDERLINE:
        return "borderline"
    else:
        return "bad"


def main(out_dir="agents/classifier/data", repeats=5, healthy=60):
    rows, runs = [], []
    seed = 0
    for fault in ["latency", "error_spike", "cpu_stress", "bad_config"]:
        for severity in ["low", "medium", "high"]:
            for onset in ["start", "mid"]:
                for _ in range(repeats):
                    run_id = f"run{seed:04d}"
                    cls = run_class_for(fault, severity)
                    rows += simulate_run(run_id, fault, severity, onset, cls, seed)
                    runs.append({"run_id": run_id, "fault": fault, "severity": severity,
                                 "onset": onset, "run_class": cls, "seed": seed})
                    seed += 1
    for _ in range(healthy):        #       (fault=None, severity=None, onset="start", run_class="healthy")
        run_id = f"run{seed:04d}"
        rows += simulate_run(run_id, None, None, "start", "healthy", seed)
        runs.append({"run_id": run_id, "fault": None, "severity": None,
                    "onset": "start", "run_class": "healthy", "seed": seed})
        seed += 1

    os.makedirs(out_dir, exist_ok=True)
    pd.DataFrame(rows).to_csv(f"{out_dir}/raw_windows.csv", index=False)
    pd.DataFrame(runs).to_csv(f"{out_dir}/runs.csv", index=False)
    print(f"{len(runs)} runs, {len(rows)} rows written to {out_dir}")

if __name__ == "__main__":
    main()

