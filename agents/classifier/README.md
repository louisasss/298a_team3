# Canary classifier (v0)

A model that looks at one analysis window of a canary release and predicts whether the canary is **healthy (0)** or **faulty (1)**. The single tool-using agent calls it as a tool during canary analysis.

> **v0 is trained on simulated data.** The simulator follows `docs/data-generation-plan.md`. Real data from fault-injected canary runs will replace it once the pipeline is running.

## Run it

From the repo root, in the dev container (Python 3.10):

```bash
pip install -r agents/classifier/requirements.txt
python agents/classifier/simulate.py    # generate simulated canary runs
python agents/classifier/features.py    # turn raw windows into features + labels
python agents/classifier/train.py       # search, train, evaluate, save results
```

The whole pipeline takes about a minute.

## What each script does

| Script | Input | Output |
|---|---|---|
| `simulate.py` | settings at the top of the file | `data/raw_windows.csv`, `data/runs.csv` |
| `features.py` | `data/raw_windows.csv` | `data/features.csv` (11 features per window) |
| `train.py` | `data/features.csv`, `data/runs.csv` | `results/` |

`train.py` splits by run (65/15/20) and holds out the bad-config fault entirely. It compares logistic regression and gradient-boosted trees with a small hyperparameter search, and scores the best model per release against a fixed threshold rule.

## Results

| File | Contents |
|---|---|
| `results/hp_search.csv` | Every hyperparameter combination tried, with validation score and fit time |
| `results/release_report.csv` | Precision, recall, false rollbacks, missed bad releases and time to detection, for the classifier and the threshold rule, on the test set and the held-out fault |
| `results/learning_curve.png` | Validation score as training data grows |
| `results/compute.json` | Number of fits, total training time, hardware |

## Notes

- `data/` is not committed. Every run has a fixed seed, so the scripts regenerate identical data.
- Fault type, severity and other run metadata are used only for splitting and reporting, never as features.
- The test set is small (about 10 bad releases), so treat the scores as indicative.