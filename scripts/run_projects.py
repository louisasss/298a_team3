from pathlib import Path
import subprocess
import time
import csv

# Temporary project max
MAX_PROJECTS = 10
PROJECT_TIMEOUT_MINUTES = 30

ROUNDS = 10
DETECTOR_TIMEOUT = 1000000

# Paths that are included
SCRIPT_DIR = Path(__file__).resolve().parent
ANALYSIS_DIR = SCRIPT_DIR.parent
DATA298_DIR = ANALYSIS_DIR.parent

IDFLAKIES_DIR = DATA298_DIR / "iDFlakies"
DOCKER_DIR = IDFLAKIES_DIR / "scripts" / "docker"

PROJECT_LIST = (ANALYSIS_DIR / "project_lists" / "comprehensive_projects.txt")

LOG_DIR = ANALYSIS_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

STATUS_FILE = LOG_DIR / "project_run_status.csv"

# Read the comprehensive projects txt 
with open(PROJECT_LIST, "r") as f:
    projects = [
        line.strip()
        for line in f
        if line.strip()
    ]

# Only use first 10 for testing
projects = projects[:MAX_PROJECTS]

print("Projects selected:", len(projects))

# Status file to check if we need to go back to it later
if not STATUS_FILE.exists():
    with open(STATUS_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "project_csv",
            "status",
            "runtime_minutes"
        ])


# Run each project with same command as example
for i, project_csv in enumerate(projects, start=1):
    print()
    print("=" * 60)
    print(f"[{i}/{len(projects)}]")
    print(project_csv)
    print("=" * 60) # visuals

    # Remove scripts/docker/ because the command already runs inside that specific folder
    project_arg = project_csv.replace("scripts/docker/","")

    command = [
        "bash",
        "create_and_run_dockers.sh",
        project_arg,
        str(ROUNDS),
        str(DETECTOR_TIMEOUT)
    ]

    print("Running:")
    print(" ".join(command))

    start = time.time()

    try:
        result = subprocess.run(
            command,
            cwd=DOCKER_DIR,
            timeout=PROJECT_TIMEOUT_MINUTES * 60
        )

        if result.returncode == 0:
            status = "COMPLETED"
        else:
            status = "FAILED"

    except subprocess.TimeoutExpired:
        status = "TIMEOUT"

    except Exception as e:
        print("Error:", e)
        status = "ERROR"

    runtime = (time.time() - start) / 60

    with open(STATUS_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            project_csv,
            status,
            round(runtime, 2)
        ])

    print("Status:", status)
    print("Runtime:", round(runtime, 2), "minutes")


print()
print("Finished.")
print("Status file:")
print(STATUS_FILE)