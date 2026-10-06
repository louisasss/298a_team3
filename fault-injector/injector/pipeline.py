# Runs the demo app's build and saves everything it prints.
#
# WHY a separate file: the harness shouldn't care HOW the pipeline runs, only
# that it gets back (exit_code, log_path). If the team later switches from
# `mvn test` to a docker compose run, only this file changes.

import os
import subprocess

# How long one pipeline run may take before we give up on it (seconds).
# Maven's first run downloads dependencies, so this is generous on purpose.
TIMEOUT_SECONDS = 600


def run(repo_path, logs_dir, run_id, env_remove=()):
    """Run `mvn -B test` in repo_path.

    Saves the full combined output (stdout + stderr) to
    logs_dir/<run_id>.log and returns (exit_code, log_path).
    env_remove lists env vars to DELETE from the run's environment
    (used by the DeleteEnvVar infra fault).
    """
    os.makedirs(logs_dir, exist_ok=True)
    log_path = os.path.join(logs_dir, run_id + ".log")

    # The pipeline always runs with a sane default environment...
    env = dict(os.environ)
    env.setdefault("SHOP_DB_URL", "jdbc:fake:memdb")

    # ...minus whatever the fault asked us to remove.
    for var in env_remove:
        env.pop(var, None)

    with open(log_path, "w") as log_file:
        # A small header so a human opening the log knows what produced it.
        log_file.write("# run: " + run_id + "\n")
        log_file.write("# command: mvn -B test\n")
        log_file.write("# cwd: " + repo_path + "\n\n")
        log_file.flush()
        cmd = ["mvn", "-B", "clean", "test"]
        if os.name == "nt":  # Windows: mvn is a .cmd script, launch via cmd.exe
            cmd = ["cmd", "/c"] + cmd
        proc = subprocess.run(
            cmd,
            cwd=repo_path,
            env=env,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            timeout=TIMEOUT_SECONDS,
        )
    return proc.returncode, log_path
