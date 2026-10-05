#!/usr/bin/env python3
"""The main loop of the fault injector.

Every full run does the same 6 steps:
  1. pick a fault (round-robin over the 4 classes, so the dataset stays balanced)
  2. snapshot the clean demo-app folder
  3. apply the fault
  4. run the pipeline (mvn test), saving the full log
  5. check the build actually failed (a fault that breaks nothing is a wasted row)
  6. write the dataset row, then restore the clean folder -- ALWAYS, even on crashes

Usage (run from the fault-injector folder):
  python injector/harness.py --list-faults        show every fault in the library
  python injector/harness.py --demo FlipConditional
                                                     apply + revert one fault, no Maven needed
  python injector/harness.py --check-clean        run the pipeline once with no fault
  python injector/harness.py --runs 8 --seed 7    full loop: 8 faults, 2 per class
"""

import argparse
import filecmp
import os
import random
import shutil
import sys
import tempfile
import time

# Make sure `from faults import ...` works no matter where you run this from.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from faults import ALL_FAULTS
import pipeline
import dataset

# All paths are derived from this file's location, so the harness works
# from any working directory.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO_APP = os.path.join(ROOT, "demo-app")
LOGS_DIR = os.path.join(ROOT, "logs")
CSV_PATH = os.path.join(ROOT, "dataset.csv")

# Fixed class rotation: run 0 -> regression, 1 -> flaky, 2 -> infra,
# 3 -> dependency, 4 -> regression again, ... Balanced by construction.
CLASS_ORDER = ["regression", "flaky", "infra", "dependency"]

# A "flaky" fault gets this many pipeline tries to show a failure.
# If it passes all of them, we record nothing (a green log is not a failure).
FLAKY_RETRIES = 5


# --------------------------------------------------------------------------
# Picking faults
# --------------------------------------------------------------------------

def pick_fault(run_index, rng):
    """Pick the fault for run number run_index (0-based)."""
    target = CLASS_ORDER[run_index % len(CLASS_ORDER)]
    candidates = [f for f in ALL_FAULTS if f.target_class == target]
    # Stubs (KillDatabase, NetworkPartition) raise NotImplementedError until
    # Docker exists, so they sit out the random rotation for now. They still
    # show up in --list-faults, clearly marked STUB.
    usable = [f for f in candidates if not f.description.startswith("STUB")]
    return rng.choice(usable)


def find_fault(name):
    for fault in ALL_FAULTS:
        if fault.name == name:
            return fault
    return None


# --------------------------------------------------------------------------
# Snapshot / restore -- the correctness-critical part
# --------------------------------------------------------------------------

def backup_tree():
    """Copy the whole clean demo-app folder into a fresh temp dir.

    WHY copy the whole folder instead of something cleverer (git stash,
    diffs): it is dead simple, obviously correct, and easy to explain at a
    checkpoint. There is no cleverness here to go wrong.
    Returns the temp dir path; the backup lives at <tmp>/demo-app.
    """
    tmp = tempfile.mkdtemp(prefix="fault-injector-clean-")
    shutil.copytree(DEMO_APP, os.path.join(tmp, "demo-app"))
    return tmp


def restore_tree(tmp):
    """Delete the (possibly sabotaged) demo-app tree and copy the clean
    backup back in its place.

    WHY delete-then-copy instead of copying over the top: copying over would
    leave behind any NEW files the fault created. Delete-then-copy guarantees
    the tree is byte-identical to the clean state, no matter what the fault
    did. This is what makes a leaked fault impossible.
    """
    shutil.rmtree(DEMO_APP)
    shutil.copytree(os.path.join(tmp, "demo-app"), DEMO_APP)
    shutil.rmtree(tmp, ignore_errors=True)


def trees_equal(dir_a, dir_b):
    """True if two folders contain exactly the same files with the same
    contents. Used by --demo to prove revert() really undid the fault."""
    cmp = filecmp.dircmp(dir_a, dir_b)
    if cmp.left_only or cmp.right_only or cmp.diff_files:
        return False
    for sub in cmp.common_dirs:
        if not trees_equal(os.path.join(dir_a, sub), os.path.join(dir_b, sub)):
            return False
    return True


# --------------------------------------------------------------------------
# Running the pipeline
# --------------------------------------------------------------------------

def run_until_failure(fault, run_id, params):
    """For flaky faults: run the pipeline up to FLAKY_RETRIES times, stopping
    at the first failure. Returns (exit_code, log_path), or (None, None) if
    every try passed (then the row is skipped -- a green log is not a
    failure, and recording one would poison the dataset)."""
    for attempt in range(1, FLAKY_RETRIES + 1):
        attempt_id = run_id if attempt == 1 else "%s-retry%d" % (run_id, attempt)
        exit_code, log_path = pipeline.run(DEMO_APP, LOGS_DIR, attempt_id,
                                           fault.env_to_remove)
        if exit_code != 0:
            if attempt > 1:
                print("  flaky fault failed on try %d (that intermittency is the point)"
                      % attempt)
            return exit_code, log_path
        print("  try %d passed (flaky faults sometimes do)" % attempt)
    return None, None


def do_run(fault, run_id, params, seed):
    """One full inject -> run -> record cycle. Returns True if a dataset row
    was written, False if the run was skipped."""
    print("run %s: fault=%s class=%s" % (run_id, fault.name, fault.target_class))
    tmp = backup_tree()
    try:
        fault.apply(DEMO_APP, params)

        if fault.target_class == "flaky":
            exit_code, log_path = run_until_failure(fault, run_id, params)
            if exit_code is None:
                print("  SKIP: fault never failed in %d tries, no row written"
                      % FLAKY_RETRIES)
                return False
        else:
            exit_code, log_path = pipeline.run(DEMO_APP, LOGS_DIR, run_id,
                                               fault.env_to_remove)
            if exit_code == 0:
                # The fault didn't break the build (a "silent" fault). A green
                # log labeled as a failure would poison the dataset, so we skip
                # it -- loudly, so nobody wonders where the row went.
                print("  SKIP: build stayed green, no row written")
                return False

        dataset.append_row(CSV_PATH, {
            "run_id": run_id,
            "fault_name": fault.name,
            "label": fault.target_class,
            "params": str(params),
            "seed": seed,
            "exit_code": exit_code,
            "log_path": log_path,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        })
        print("  row written (exit code %d)" % exit_code)
        return True
    finally:
        # ALWAYS restore, even if the pipeline crashed halfway. A half-applied
        # fault leaking into the next run would silently mislabel every later
        # row -- this finally block is the most important correctness code in
        # the whole project.
        try:
            # revert() is only a safety net; the tree restore below is the real
            # guarantee, so a revert hiccup is a warning, not a crash.
            fault.revert(DEMO_APP)
        except Exception as e:
            print("  warning: revert() complained (%s); tree restore still runs" % e)
        restore_tree(tmp)


# --------------------------------------------------------------------------
# Modes
# --------------------------------------------------------------------------

def list_faults():
    print("Fault library (%d faults):\n" % len(ALL_FAULTS))
    for fault in ALL_FAULTS:
        print("  %-22s [%s]" % (fault.name, fault.target_class))
        print("      %s" % fault.description)
    print("\nAdd a new fault: copy the nearest one in injector/faults/, then")
    print("add it to ALL_FAULTS in injector/faults/__init__.py.")


def demo_mode(name):
    """Apply + revert one fault without running Maven. Proves the file-level
    logic works (and that revert really undoes apply) on machines without
    Java/Maven/Docker."""
    fault = find_fault(name)
    if fault is None:
        print("unknown fault: " + name)
        print("available: " + ", ".join(f.name for f in ALL_FAULTS))
        return
    print("demo: %s [%s]" % (fault.name, fault.target_class))
    tmp = backup_tree()
    try:
        fault.apply(DEMO_APP, {"seed": 0})
        print("  applied OK")
        fault.revert(DEMO_APP)
        print("  reverted OK")
        if trees_equal(os.path.join(tmp, "demo-app"), DEMO_APP):
            print("  verified: tree is identical to the pre-fault state")
        else:
            print("  WARNING: tree differs after revert() "
                  "(the backup restore in real runs would still fix it)")
    finally:
        restore_tree(tmp)


def check_clean_mode():
    """Run the pipeline once with NO fault. Must be green -- if the clean tree
    doesn't pass, every later label is suspect. (The 10-consecutive-green gate
    from the README is just this, repeated.)"""
    exit_code, log_path = pipeline.run(DEMO_APP, LOGS_DIR, "clean-check")
    print("clean run exit code: %d" % exit_code)
    print("log: %s" % log_path)
    if exit_code == 0:
        print("CLEAN: the un-sabotaged pipeline passes.")
    else:
        print("NOT CLEAN: fix the demo app / pipeline before injecting faults.")


def ensure_maven():
    """Fail fast with a helpful message instead of a traceback."""
    if shutil.which("mvn") is None:
        print("mvn not found. The full loop needs a JDK + Maven.")
        print("File-level modes still work here: --list-faults and --demo <Name>.")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Fault injector: deliberately break the demo app, "
                    "record the failure, build a labeled dataset.")
    parser.add_argument("--list-faults", action="store_true",
                        help="print the fault library and exit")
    parser.add_argument("--demo", metavar="FAULT_NAME",
                        help="apply + revert one fault without Maven")
    parser.add_argument("--check-clean", action="store_true",
                        help="run the pipeline once with no fault")
    parser.add_argument("--runs", type=int, metavar="N",
                        help="full loop: inject N faults and record dataset rows")
    parser.add_argument("--seed", type=int, default=7,
                        help="random seed (default 7); same seed = same fault order")
    args = parser.parse_args()

    if args.list_faults:
        list_faults()
    elif args.demo:
        demo_mode(args.demo)
    elif args.check_clean:
        ensure_maven()
        check_clean_mode()
    elif args.runs:
        ensure_maven()
        rng = random.Random(args.seed)
        written = 0
        for i in range(args.runs):
            run_id = "run-%03d" % (i + 1)
            fault = pick_fault(i, rng)
            params = {"seed": args.seed + i}
            try:
                if do_run(fault, run_id, params, args.seed):
                    written += 1
            except NotImplementedError as e:
                # A stub fault slipped through (shouldn't happen -- pick_fault
                # filters them -- but fail safe, not silent).
                print("  SKIP (not implemented yet): %s" % e)
        print("\ndone: %d dataset rows written to %s" % (written, CSV_PATH))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
