# Appends one row per pipeline run to dataset.csv.
#
# WHY these columns:
#   run_id / timestamp / seed  -> every row is reproducible; you can re-run
#                                 the exact same fault and compare.
#   fault_name + label          -> the ground truth. We caused the failure,
#                                 so the label is known, not guessed.
#   params                     -> what the fault was configured with.
#   exit_code + log_path        -> lets us check the failure later from the
#                                 log alone, without rerunning anything.

import csv
import os

HEADER = ["run_id", "fault_name", "label", "params", "seed",
          "exit_code", "log_path", "timestamp"]


def append_row(csv_path, row):
    """Append one dataset row (a dict). Creates the file with a header
    the first time."""
    file_exists = os.path.exists(csv_path)
    with open(csv_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=HEADER)
        if not file_exists:
            writer.writeheader()
        # Only the known columns are written, in a fixed order.
        writer.writerow({key: row.get(key, "") for key in HEADER})
