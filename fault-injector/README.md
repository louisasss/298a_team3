# Fault Injector

**The one-sentence version:** this is the saboteur inside our toy software factory.
It deliberately breaks our demo app in controlled ways, records how the build
fails, and produces the labeled dataset our failure classifier trains on.

**Why we may need it:** our classifier must tell apart 4 kinds of failures --
flaky test, real regression, infrastructure, dependency. No public dataset gives
us all 4 with trustworthy labels (we checked: BugSwarm is 90% regression,
Defects4J has bugs but no CI logs, TravisTorrent's raw logs are gone). The
injector solves this with one trick: **it causes the failure, so it knows the
label with certainty.** No guessing, no hand-labeling.

## How the loop works

Each run does the same 6 steps (`injector/harness.py`):

1. **Pick a fault** -- round-robin over the 4 classes, so the dataset stays
   balanced no matter how many runs you do (run 0 = regression, 1 = flaky,
   2 = infra, 3 = dependency, 4 = regression again...).
2. **Snapshot** the clean `demo-app/` folder into a temp backup.
3. **Apply the fault** -- e.g. flip a conditional in the Java code.
4. **Run the pipeline** (`mvn -B test`), saving the full log to `logs/`.
5. **Verify the build actually failed.** A fault that breaks nothing produces a
   green log, and a green log labeled "failure" would poison the dataset -- so
   those runs are skipped loudly, not recorded. (Flaky faults get up to 5 tries,
   because passing sometimes is their whole point.)
6. **Write one row** to `dataset.csv`, then **restore the clean folder** --
   always, even if the pipeline crashed halfway. The restore is in a `finally`
   block: a half-applied fault leaking into the next run would silently
   mislabel every later row, so this is the most important correctness code
   in the project.

## How to run it

From the `fault-injector/` folder:

```bash
# See every fault in the library (works anywhere, no Java/Maven needed)
python injector/harness.py --list-faults

# Try one fault's file editing without running Maven (also works anywhere)
python injector/harness.py --demo FlipConditional

# Run the pipeline once with NO fault -- must be green.
# If the clean tree doesn't pass, every later label is suspect.
python injector/harness.py --check-clean

# The full loop: 8 faults (2 per class), seed 7 for reproducibility
python injector/harness.py --runs 8 --seed 7
```

The full loop needs a JDK + Maven (`--check-clean` and `--runs`). The file-level
modes (`--list-faults`, `--demo`) work on any machine with Python.

## How to add a new fault

1. Open the file matching your failure class in `injector/faults/`
   (`regression.py`, `flaky.py`, `infra.py`, `dependency.py`).
2. Copy the nearest existing fault class. Fill in four things:
   - `name` -- e.g. `"MyNewFault"`
   - `target_class` -- one of `"regression"`, `"flaky"`, `"infra"`, `"dependency"`
   - `description` -- one line saying what it breaks
   - `apply()` / `revert()` -- break it, then put it back (use `replace_exact`
     from `base.py`: exact-match text edits that fail loudly if the anchor
     text isn't found, so a silently-skipped edit can never poison the data)
3. Add it to `ALL_FAULTS` in `injector/faults/__init__.py`.
4. Test it: `python injector/harness.py --demo MyNewFault` must print
   "verified: tree is identical to the pre-fault state".

**If you're writing a flaky fault**,  first: the injected problem must *straddle* 
the failure threshold (some runs pass, some fail). Too strong = every run fails = that's a
regression in a costume.

## The dataset

`dataset.csv` columns: `run_id, fault_name, label, params, seed, exit_code,
log_path, timestamp`. The `label` is ground truth (we caused it). Full logs
live in `logs/`.A future step is running our log parser over these logs to 
extract failed tests / stage / exception into extra columns.

`parser/parse_logs.py` turns every log into one feature row in `features.csv`:
stage (dependency/compile/test), exception, failed test names, Surefire
counts, and one evidence line per log. The label is carried over untouched --
the parser never guesses it. Run it from `fault-injector/` with
`python parser/parse_logs.py`.

`features.csv` columns: `run_id, fault_name, label, stage, exception,
failed_tests, n_failed_tests, tests_run, failures, errors, skipped,
failure_signal, log_path`. 

**Splits:** when we train, split by fault name (or by app module), never
randomly -- the classifier must generalize to *unseen* fault types, not
memorize our specific edits.

## What's stubbed / future work

- `KillDatabase` and `NetworkPartition` (in `injector/faults/infra.py`) need a
  Docker daemon -- they're written as clearly-marked stubs. `docker-compose.yml`
  defines the app + db services they'll use.
- **The 10-green-run gate:** before generating the real dataset, `--check-clean`
  should pass 10 times in a row. A pipeline with ambient flakiness makes every
  flaky label suspect.
- **Scale-up:** run headless on a cloud VM, a few hundred rows per class, then
  train the classifier. 
