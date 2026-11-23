# Data Generation Plan

## Goal
Generate labeled canary runs to train a classifier that predicts promote/healthy (0) or rollback/faulty (1) for each analysis window. Window length = the AnalysisTemplate window (owned by Pragya).


## Environment
ParcelPost [+ second app, TBD] on our Kubernetes cluster. Argo Rollouts canary steps: 10% → 25% → 50% → 100%. Metrics per the ParcelPost metrics contract: error rate, p95 latency and traffic per version, from Prometheus.


## Unit of data
One sample row of data consists of one row per analysis window (one row per minute during canary). We selected one row per analysis window because the temporal component allows us to measure time to detection.

**Features:**
| Feature | Definition | Why |
| --- | --- | --- |
| error-rate difference | (canary error-rate) - (stable error-rate) | Core signal: is the canary failing more than stable right now? |
| p95 latency ratio | (canary p95 latency) / (stable p95 latency) | Catches the slowest requests, timeouts pool exhaustion |
| p50 latency ratio | (canary p50 latency) / (stable p50 latency) | Catches requests getting slower, CPU stress |
| stable request count | number of requests answered by the stable in this window | Model learns not to trust small samples because low traffic makes rates noisy |
| canary request count | number of requests answered by the canary in this window | Model learns not to trust small samples because low traffic makes rates noisy |
| minutes since canary start | (window start time) - (time the canary's first step began) | Allows model to learn warm-up instead of rolling back over it |
| current canary weight step | current Argo Rollouts canary step percentage | Tells the model how much traffic the canary is handling |
| change in error-rate difference since previous window | Δ error-rate difference = (this window’s error-rate difference) − (the previous window’s error-rate difference) | catches faults that are getting worse, time to detection |
| change in p95 latency ratio since previous window | Δ p95 latency ratio = (this window’s p95 latency ratio) − (the previous window’s p95 latency ratio) | catches faults that are getting worse, time to detection |
| change in p50 latency ratio since previous window | Δ p50 latency ratio = (this window’s p50 latency ratio) − (the previous window’s p50 latency ratio) | catches faults that are getting worse, time to detection |
| worst route's error-rate difference | max(canary error rate - stable error rate per route); only routes with at least 10 requests in the window count | catches potential problems on one route that the overall average hides | 

**Edge cases:** When there are no requests for either canary or stable versions in a window, the window is excluded from training and evaluation datasets.

**Leakage:** Features use only information available to the live pipeline at decision time; run metadata (fault type, severity, onset time, seed, run ID) is never used as a feature.


## Scenarios
| Dimension	| Values |
| --- | --- |
| Fault type | latency, error spike, CPU stress, bad config |
| Severity | low / medium / high |
| Onset	| start of canary, or mid-canary |
| Healthy releases | no fault; harmless code change (new SHA) |

Bad config is injected by changing a value in the canary's ConfigMap. A bad config is either:
* Database connection pool set too small.
* Timeout to a dependency set too low. 

Faults are injected into canary pods only: Chaos Mesh for stress, and a environment variables on the canary pods for latency and errors. Before generating, each fault type is checked once to confirm it actually shows up in the metrics.


## Noise
The load generator varies request rate ±30% and route mix, with random bursts. The first window after deploy includes warm-up. Each run has its own random seed.


## Labels
* **SLO:** set from 5 healthy baseline runs as [p95 > 2× healthy p95 or error rate > 1%]. Frozen before calibration.
* **Calibration:** each fault × severity is run 3 times and marked bad, borderline or harmless against the SLO. Borderline combinations are [included in the test set and scored separately].
* **Run label:** taken from the calibration table based on what was injected, never from the run’s own metrics.
* **Window label:** before onset = 0. After onset in a bad run = 1. The window containing the onset is excluded. Windows with no data are inconclusive and excluded.

## Splits (by run, never by window)
* **Held-out fault:** Propose hold out bad config fault type because it looks different from the infrastructure faults so we know the model isn't just learning patterns of fault types with similar patterns.
* **Held-out service:** [TBD, pending the services question]. 
* **Split:** The remaining runs are split 65/15/20 train/val/test.
* **Leakage check:** no run ID appears in two splits.

## Volume
[4 faults × 3 severities × 2 onsets × 5 repeats = 120 bad runs, + 60 healthy runs]. At [~7 min per run, 2 in parallel] that’s about [10.5 hours] of cluster time. Target: at least 15 bad releases in each test set.

## Storage
Two layers of data, raw which is never changed, and derived, which is computed from data in the raw layer. Raw data is never modified; all features are produced by a versioned script, so the features can be changed and recomputed without re-running any canaries. All data stored in GCS.

**Raw layer**
* request log table: one row per request (run_id, timestamp, version (canary or stable, from the response header), route, status code, latency)
* prometheus export table: each run’s metric series, saved when the run ends
* run metadata table: run_id, service, fault, severity, onset_time, SHAs, load profile, seed

**Derived layer**
* Window features: One Parquet table of windows computed from the raw layer (run_id, window_start, features, label)
* Judge inputs: Mann-Whitney reads the request latencies per window from the raw layer, while the threshold template and the classifier read the window features


## Evaluation use
Every test run is scored by three judges: the Argo threshold AnalysisTemplate, a Mann-Whitney judge, and our classifier. All three see the same windows.

Each judge’s decisions are scored per release (a release counts as rolled back at the first window the judge flags): precision, recall, missed bad releases and false rollback rate measure accuracy; time to detection is minutes from onset to the first flagged window. Borderline and held-out runs are reported separately.

The ablation runs the single agent on the same test runs with and without the classifier tool, with all other variables (model, prompt and budget) unchanged, and compares the same metrics; the classifier.called field confirms whether the classifier was called.

## Timeline
Data generation requires a working canary with traffic routing, load generator, and Prometheus scraping. Generation can start once team Linear issues T3-69, T3-78, T3-83 are complete and Chaos Mesh is installed in the cluster (Sang Ah owns). Data generation is expected to take ((4 fault types x 3 severity levels x 3 runs) x 7 minutes) + (5 baseline healthy runs x 7 minutes) + approx 10.5 hours of generation + 7 hours for re-runs when something breaks = 22.3 hours total. 