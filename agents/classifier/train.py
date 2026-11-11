import json
import platform
import time
import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score
from sklearn.model_selection import ParameterGrid
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


from features import FEATURES

DATA = "agents/classifier/data"

# 1. Load the features and attach each run's metadata
df = pd.read_csv(f"{DATA}/features.csv")
runs = pd.read_csv(f"{DATA}/runs.csv")
df = df.merge(runs[["run_id", "fault", "run_class"]], on="run_id")   # metadata for splitting only, never a feature

# 2. Set aside the held-out fault
held_out = df[df.fault == "bad_config"]          # the held-out fault: never trained on
rest = df[df.fault != "bad_config"]

# 3. Shuffle the run IDs (runs, not windows)
run_ids = rest.run_id.unique().tolist()
rng = np.random.default_rng(42)
rng.shuffle(run_ids)

# 4. Cut the shuffled list at 65% and 80%
n = len(run_ids)
a = int(n * 0.65)
b = int(n * 0.80)       # 65% train + 15% val
train_ids, val_ids, test_ids = run_ids[:a], run_ids[a:b], run_ids[b:]       #[:a] everything before position 97, [a:b] position 97 to 120, [b:] position 120 on

# 5. Turn each list of run IDs into a table of windows (not split by runs)
train = rest[rest.run_id.isin(train_ids)]
val = rest[rest.run_id.isin(val_ids)]
test = rest[rest.run_id.isin(test_ids)]

# 6. Leakage check: stop if any run is in two splits
assert not (set(train_ids) & set(val_ids)), "run in train and val"
assert not (set(train_ids) & set(test_ids)), "run in train and test"
assert not (set(val_ids) & set(test_ids)), "run in val and test"

# 7. Summary for your data slide
for name, part in [("train", train), ("val", val), ("test", test), ("held-out", held_out)]:
    print(f"{name:9} {part.run_id.nunique():3} runs  {len(part):4} windows  {part.label.mean():.0%} faulty")


def make_model(name, params):
    """select either the logistic regression or gradient boosting model"""
    if name == "logreg":
        # logistic regression needs features on similar scales, so standardise first
        return make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000, **params))
    return HistGradientBoostingClassifier(random_state=0, **params)

# grid of hyperparameter combinations we are trying
GRIDS = {
    "logreg": {"C": [0.01, 0.1, 1, 10], "class_weight": [None, "balanced"]},
    "gboost": {"learning_rate": [0.05, 0.1], "max_depth": [2, 3, 5], "max_iter": [100, 200]},
}

# 8. run models for every combination of hyperparameters we're testing to find best model
results = []
for name, grid in GRIDS.items():
    for params in ParameterGrid(grid):          # every combination in the grid: 4x2=8 for logistic regression, 2x3x2=12 for boosting, 20 models total
        model = make_model(name, params)
        t0 = time.perf_counter()            # start compute consumed counter
        model.fit(train[FEATURES], train.label)     # trains on train set only
        fit_seconds = time.perf_counter() - t0      # end compute consumed counter
        val_scores = model.predict_proba(val[FEATURES])[:, 1]       # each validation window's probability of being faulty
        results.append({"model": name, "params": params, **params,
                        "val_ap": average_precision_score(val.label, val_scores),
                        "fit_seconds": fit_seconds})

# 9. store hyperparameters in table
search = pd.DataFrame(results).sort_values("val_ap", ascending=False)       # hyperparameter table
print(search.drop(columns="params").head(6).to_string(index=False))
print(f"{len(search)} fits, {search.fit_seconds.sum():.1f} s total")        # display total time taken by task

# 10. retrieve best vaildation score from hyperparameters table
best = search.iloc[0]                                   # top row = best validation score
train_val = pd.concat([train, val])         # combine train and validation data to train final model, test data untouched
final = make_model(best["model"], best["params"])
final.fit(train_val[FEATURES], train_val.label)

# which window each run's fault started with, for time to detection
ONSET_WINDOW = runs.set_index("run_id").onset.map({"start": 0, "mid": 4})       # window 0 for "start" runs, window 4 (50% step) for "mid" runs 

def classifier_flags(part):
    """Flag a window when the classifier thinks it's at least 50% likely to be faulty."""
    # predict_proba gives [P(healthy), P(faulty)] for each window; [:, 1] keeps P(faulty).
    return final.predict_proba(part[FEATURES])[:, 1] >= 0.5

def threshold_flags(part):
    """
    Baseline is a fixed rule (like Argo AnalysisTemplate), flag window if:
    - the canary's error rate is more than 1 point above stable's error rate
    OR
    - canary's p95 latency is more than 2x stable's
    """
    return ((part.error_rate_diff > 0.01) | (part.p95_ratio > 2.0)).to_numpy()      # | means or, applied to all rows at one time

def release_metrics(part, flags):
    """Score a judge's flags per release (per run)"""
    p = part.assign(flag=flags)     # attach current judges flag to each window
    per_run = p.groupby("run_id").agg(      # squash each run's window into one row
        run_class=("run_class", "first"),   # run_class = the run's true class (bad, harmless, borderline, healthy)
        rolled_back=("flag", "any")         # rolled_back = true if any window was flagged (same as how Argo behaves)
        )
    per_run["first_flag"] = p[p.flag].groupby("run_id").window.min()         # first flagged window per run, tells us WHEN the judge reacted. runs with no flagged window get empty value

    # group runs by right answer label
    bad = per_run[per_run.run_class == "bad"]                           # should be rolled back
    good = per_run[per_run.run_class.isin(["healthy", "harmless"])]     # should be promoted
    borderline = per_run[per_run.run_class == "borderline"]             # borderline reported separately

    # caught: bad releases correctly rolled back.
    # false_alarms: good releases wrongly rolled back.
    caught, false_alarms = bad.rolled_back.sum(), good.rolled_back.sum()        # (.sum() on True/False counts the Trues.)

    # Time to detection, only for bad releases that were caught
    caught_runs = bad[bad.rolled_back]
    minutes = (caught_runs.first_flag - ONSET_WINDOW[caught_runs.index]).clip(lower=0)      # .clip(lower=0) turns any early flag (before onset) into 0 instead of a negative.

    return {"bad releases": len(bad), 
            "good releases": len(good),
            "precision": caught / (caught + false_alarms) if caught + false_alarms else np.nan,     # of the rolled back releases, how many were really bad?
            "recall": caught / len(bad),        # of the bad releases, how many were caught?
            "false rollback rate": false_alarms / len(good),        # of the good releases, how many were wrongly rolled back?
            "missed bad": len(bad) - caught,        # how many bad releases were promoted anyways?
            "time to detection (min)": minutes.mean(),      # avg minutes from fault onset to the first flag
            "borderline rolled back": borderline.rolled_back.mean() if len(borderline) else np.nan}     # portion of borderline releases rolled back

# 11. score both judges on both evaluation sets:
#   test                - faults the classifier was trained on, in unseen runs
#   held-out bad config - a fault type the classifier never saw (generalization test)
rows = []
for set_name, part in [("test", test), ("held-out bad config", held_out)]:
    for judge, flag_fn in [("classifier", classifier_flags), ("threshold rule", threshold_flags)]:
        rows.append({"set": set_name, "judge": judge, **release_metrics(part, flag_fn(part))})

# one row per (set, judge)
report = pd.DataFrame(rows)
print(report.round(2).to_string(index=False))

# create folder for results 
OUT = "agents/classifier/results"
os.makedirs(OUT, exist_ok=True)

# 12. train the winning settings on 20%, 40%, 60%, 80%, 100% of the training RUNS
curve = []
for frac in [0.2, 0.4, 0.6, 0.8, 1.0]:
    for rep in range(3):        # repeat each size 3 times with different random subsets to show variation (shaded band in plot)
        sub_rng = np.random.default_rng(rep)
        n_runs = max(2, int(len(train_ids) * frac))
        ids = sub_rng.choice(train_ids, size=n_runs, replace=False)   # pick runs, not windows
        sub = train[train.run_id.isin(ids)]
        m = make_model(best["model"], best["params"]).fit(sub[FEATURES], sub.label)
        curve.append({
            "train_runs": n_runs,
            "train_ap": average_precision_score(sub.label, m.predict_proba(sub[FEATURES])[:, 1]),
            "val_ap": average_precision_score(val.label, m.predict_proba(val[FEATURES])[:, 1]),
        })
curve = pd.DataFrame(curve)

# compute average and spread across the 3 repeats, for each training size
mean = curve.groupby("train_runs")[["train_ap", "val_ap"]].mean()
std = curve.groupby("train_runs")[["train_ap", "val_ap"]].std()
print(mean.round(3))

# plot: one line per score, with a shaded band of plus or minus one standard deviation
fig, ax = plt.subplots(figsize=(6, 4))
for col, label in [("train_ap", "training"), ("val_ap", "validation")]:
    ax.plot(mean.index, mean[col], marker="o", label=label)
    ax.fill_between(mean.index, mean[col] - std[col], mean[col] + std[col], alpha=0.2)
ax.set_xlabel("training runs")
ax.set_ylabel("average precision")
ax.set_title("Canary classifier v0 learning curve (simulated data)")
ax.legend()
fig.tight_layout()
fig.savefig(f"{OUT}/learning_curve.png", dpi=150)

# compute consumed
compute = {
    "search_fits": len(search),
    "search_seconds": round(search.fit_seconds.sum(), 1),
    "hardware": platform.platform(),
    "cpus": os.cpu_count(),
    "python": platform.python_version(),
}
with open(f"{OUT}/compute.json", "w") as f:
    json.dump(compute, f, indent=2)

# save the tables
search.drop(columns="params").to_csv(f"{OUT}/hp_search.csv", index=False)
report.to_csv(f"{OUT}/release_report.csv", index=False)
print(f"Results saved to {OUT}")