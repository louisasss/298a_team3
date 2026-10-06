"""Turn injector Maven logs into a feature table for the classifier.

Reads dataset.csv, parses the log each row points to, and writes
features.csv -- one row per dataset row, label carried over, plus:

  stage          where Maven died: dependency, compile, or test
  exception      Java exception name (AssertionError, ...); for compile
                 failures a normalized token like cannot-find-symbol
  failed_tests   failing test names, ";"-joined ("" when no tests ran)
  n_failed_tests how many tests failed or errored
  tests_run, failures, errors, skipped   Surefire counts (0 before tests)
  failure_signal one evidence line from the log

Patterns learned from real injector logs:
surefire 3.2.5, maven-compiler-plugin 3.13.0, JUnit 4.

Usage (from the fault-injector/ folder):
    python parser/parse_logs.py
"""

import csv
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))  # parser/
ROOT = os.path.dirname(HERE)                        # fault-injector/
DATASET_CSV = os.path.join(ROOT, "dataset.csv")
FEATURES_CSV = os.path.join(ROOT, "features.csv")

# "Tests run: 6, Failures: 3, Errors: 0, Skipped: 0"
COUNTS_RE = re.compile(
    r"Tests run:\s*(\d+),\s*Failures:\s*(\d+),\s*Errors:\s*(\d+),\s*Skipped:\s*(\d+)"
)

# "[ERROR] com.example.shop.OrderServiceTest.totalIncludesTax -- Time elapsed: 0.012 s <<< FAILURE!"
TEST_LINE_RE = re.compile(
    r"^\[ERROR\]\s+([\w.]+)\.(\w+)\s+-- Time elapsed.*<<<\s+(FAILURE|ERROR)!"
)

# Summary fallback: "[ERROR]   OrderServiceTest.bulkDiscountAppliesAtExactlyTen:27 expected:<90.0> ..."
SUMMARY_TEST_RE = re.compile(r"^\[ERROR\]\s+([A-Za-z_]\w*)\.([A-Za-z_]\w*):\d+\s")

# Exception line: "java.lang.AssertionError: expected:<108.0> but was:<109.0>"
EXCEPTION_RE = re.compile(r"((?:\w+\.)*\w+(?:Exception|Error|Failure))(?::\s*(.*))?")

# Compile-stage failures have no Java exception; normalize the compiler message
COMPILE_KINDS = [
    ("cannot-find-symbol", re.compile(r"cannot find symbol")),
    ("package-does-not-exist", re.compile(r"package .* does not exist")),
    ("bad-source-release", re.compile(r"invalid (source|target) release")),
]

# Results summary: "[ERROR]   OrderServiceTest.totalIncludesTax:41 » NullPointer"
SUMMARY_SIGNAL_RE = re.compile(r"^\[ERROR\]\s+[A-Za-z_]\w*\.[A-Za-z_]\w*:\d+\s+")

# Maven boilerplate lines are not evidence
BOILERPLATE = (
    "[Help 1]",
    "re-run Maven",
    "Please refer",
    "For more information",
    "To see the full stack",
)


def find_stage(lines, text):
    """Where did Maven die? Most specific signals first."""
    failed_goal = next(
        (ln for ln in lines if "Failed to execute goal" in ln), ""
    )
    if "Could not resolve dependencies" in text or "Non-parseable POM" in text:
        return "dependency"
    if "maven-compiler-plugin" in failed_goal or "COMPILATION ERROR" in text:
        return "compile"
    if "Tests run:" in text:
        return "test"
    return "unknown"


def find_failed_tests(lines):
    """Test names from the per-test lines; fall back to the summary section."""
    tests = []
    for ln in lines:
        m = TEST_LINE_RE.match(ln.strip())
        if m and m.group(2) not in tests:
            tests.append(m.group(2))
    if not tests:
        for ln in lines:
            m = SUMMARY_TEST_RE.match(ln.strip())
            if m and m.group(2) not in tests:
                tests.append(m.group(2))
    return tests


def find_exception(lines):
    """First exception line after a failing test line."""
    for i, ln in enumerate(lines):
        if not TEST_LINE_RE.match(ln.strip()):
            continue
        for follow in lines[i + 1:]:
            s = follow.strip()
            if not s or s.startswith("at ") or s.startswith("Caused by:"):
                continue
            m = EXCEPTION_RE.match(s)
            if m:
                return m.group(1).split(".")[-1]
            break
    return ""


def find_counts(lines):
    """Surefire counts from the Results summary (last match wins)."""
    for ln in reversed(lines):
        m = COUNTS_RE.search(ln)
        if m:
            return tuple(int(g) for g in m.groups())
    return (0, 0, 0, 0)


def find_signal(lines):
    """Best single evidence line: the Results summary line for test
    failures; otherwise the first [ERROR] line that isn't boilerplate."""
    for ln in lines:
        if SUMMARY_SIGNAL_RE.match(ln.strip()):
            return ln.strip()[:200]
    for ln in lines:
        s = ln.strip()
        if s.startswith("[ERROR]") and not any(b in s for b in BOILERPLATE):
            return s[:200]
    return ""


def parse_log(path):
    with open(path, errors="replace",) as f:
        lines = f.read().splitlines()
    text = "\n".join(lines)

    stage = find_stage(lines, text)
    failed_tests = find_failed_tests(lines)
    exception = find_exception(lines)
    if not exception and stage == "compile":
        for token, rx in COMPILE_KINDS:
            if rx.search(text):
                exception = token
                break
    tests_run, failures, errors, skipped = find_counts(lines)

    return {
        "stage": stage,
        "exception": exception,
        "failed_tests": ";".join(failed_tests),
        "n_failed_tests": len(failed_tests),
        "tests_run": tests_run,
        "failures": failures,
        "errors": errors,
        "skipped": skipped,
        "failure_signal": find_signal(lines),
    }


def main():
    with open(DATASET_CSV, newline="") as f:
        reader = csv.DictReader(f)
        dataset_rows = []
        for rec in reader:
            if None in rec:  # params held a comma; glue the split pieces back
                rec["params"] = ",".join([rec["params"]] + rec.pop(None))
            dataset_rows.append(rec)

    out_fields = [
        "run_id", "fault_name", "label", "stage", "exception",
        "failed_tests", "n_failed_tests", "tests_run", "failures",
        "errors", "skipped", "failure_signal", "log_path",
    ]
    stage_counts = {}
    with open(FEATURES_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        for rec in dataset_rows:
            log_path = rec["log_path"]
            feat = parse_log(log_path) if os.path.exists(log_path) else {}
            row = {
                "run_id": rec["run_id"],
                "fault_name": rec["fault_name"],
                "label": rec["label"],
                "log_path": log_path,
            }
            row.update(feat)
            row = {k: row.get(k, "") for k in out_fields}
            writer.writerow(row)
            stage_counts[row["stage"]] = stage_counts.get(row["stage"], 0) + 1
            print(f"{rec['run_id']}: {rec['fault_name']} -> "
                  f"stage={row['stage']} exception={row['exception']} "
                  f"failed_tests={row['n_failed_tests']}")

    print(f"\nwrote {len(dataset_rows)} feature rows to {FEATURES_CSV}")
    print("stage distribution:", stage_counts)


if __name__ == "__main__":
    main()
