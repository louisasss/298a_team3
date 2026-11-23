"""Data statistics plots for Workbook 2, section 3.6.

Run from the repo root after simulate.py and features.py:
    python agents/classifier/plots.py
Writes three PNGs to agents/classifier/results/.
"""
import os

import matplotlib

matplotlib.use("Agg")  # save images without a screen (dev container)
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from features import FEATURES

DATA = "agents/classifier/data"
OUT = "agents/classifier/results"
os.makedirs(OUT, exist_ok=True)

feat = pd.read_csv(f"{DATA}/features.csv")
runs = pd.read_csv(f"{DATA}/runs.csv")

HEALTHY, FAULTY = "#4C78A8", "#E45756"


# 1. Imbalance: windows by label, and runs by class
fig, axes = plt.subplots(1, 2, figsize=(10, 4))

counts = feat.label.value_counts().sort_index()
bars = axes[0].bar(["healthy (0)", "faulty (1)"], counts.values, color=[HEALTHY, FAULTY])
axes[0].bar_label(bars, labels=[f"{v} ({v / counts.sum():.1%})" for v in counts.values])
axes[0].set_title("Windows by label")
axes[0].set_ylabel("windows")

order = ["healthy", "harmless", "borderline", "bad"]
run_counts = runs.run_class.value_counts().reindex(order)
bars = axes[1].bar(order, run_counts.values, color=[HEALTHY, HEALTHY, "#F2A93B", FAULTY])
axes[1].bar_label(bars)
axes[1].set_title("Runs by class")
axes[1].set_ylabel("runs")

fig.suptitle("Class balance (simulated v0 data)")
fig.tight_layout()
fig.savefig(f"{OUT}/class_balance.png", dpi=150)
plt.close(fig)


# 2. Distributions: key features, healthy vs faulty windows
key = ["p95_ratio", "p50_ratio", "error_rate_diff", "worst_route_error_diff"]
fig, axes = plt.subplots(2, 2, figsize=(10, 7))
for ax, col in zip(axes.ravel(), key):
    bins = np.linspace(feat[col].min(), feat[col].max(), 30)
    ax.hist(feat.loc[feat.label == 0, col], bins=bins, alpha=0.6, color=HEALTHY, label="healthy (0)")
    ax.hist(feat.loc[feat.label == 1, col], bins=bins, alpha=0.6, color=FAULTY, label="faulty (1)")
    ax.set_title(col)
    ax.set_ylabel("windows")
axes[0, 0].legend()
fig.suptitle("Feature distributions by label (simulated v0 data)")
fig.tight_layout()
fig.savefig(f"{OUT}/feature_distributions.png", dpi=150)
plt.close(fig)

# 3. Correlation: every feature and the label, as a heatmap
corr = feat[FEATURES + ["label"]].corr()
fig, ax = plt.subplots(figsize=(9, 8))
im = ax.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1)
ax.set_xticks(range(len(corr)))
ax.set_xticklabels(corr.columns, rotation=60, ha="right")
ax.set_yticks(range(len(corr)))
ax.set_yticklabels(corr.columns)
for i in range(len(corr)):
    for j in range(len(corr)):
        v = corr.iloc[i, j]
        ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=7,
                color="white" if abs(v) > 0.6 else "black")
fig.colorbar(im, ax=ax, shrink=0.8, label="Pearson correlation")
ax.set_title("Correlation between features and label (simulated v0 data)")
fig.tight_layout()
fig.savefig(f"{OUT}/correlation.png", dpi=150)
plt.close(fig)

print(f"Saved class_balance.png, feature_distributions.png and correlation.png to {OUT}")