# Every fault in the library follows this same tiny shape.
#
# A fault is just: a name, the failure class it produces, and two actions --
# apply() breaks something, revert() puts it back.
#
# WHY a shared shape: the harness loop doesn't need to know what a fault does
# inside. It just calls apply(), runs the pipeline, calls revert(). Every new
# fault plugs into the same loop without touching the harness.

class Fault:
    # Human-readable name, e.g. "FlipConditional". Shows up in dataset.csv.
    name = "UnnamedFault"

    # One of: "regression", "flaky", "infra", "dependency".
    # This IS the ground-truth label for the dataset row.
    target_class = "regression"

    # One line for `harness.py --list-faults`, so a teammate can see what exists.
    description = "No description yet."

    # Break something. repo_path points at the demo-app folder.
    # params is a dict (e.g. {"seed": 7}) so runs stay reproducible.
    def apply(self, repo_path, params):
        raise NotImplementedError("each fault must implement apply()")

    # Undo exactly what apply() did. 
    def revert(self, repo_path):
        raise NotImplementedError("each fault must implement revert()")

    # Env vars this fault wants REMOVED from the pipeline's environment.
    # Empty for almost every fault -- only DeleteEnvVar uses it. Removing
    # (not just emptying) matters: Config.getDbUrl() treats "missing" as the
    # failure, exactly like a real deploy with a forgotten env var.
    env_to_remove = []


def replace_exact(path, old, new):
    """Replace one exact string in a file. Loud errors on purpose.

    """
    with open(path) as f:
        content = f.read()
    if old not in content:
        raise ValueError("anchor text not found in " + path + ":\n" + old)
    count = content.count(old)
    if count != 1:
        raise ValueError(
            "anchor text found " + str(count) + " times in " + path
            + " -- it must appear exactly once, or the fault is ambiguous")
    with open(path, "w") as f:
        f.write(content.replace(old, new))
