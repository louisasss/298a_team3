# Infra faults: the ENVIRONMENT is broken, not the code.


import os
from .base import Fault, replace_exact

PROPS = os.path.join("src", "main", "resources", "application.properties")


class DeleteEnvVar(Fault):
    name = "DeleteEnvVar"
    target_class = "infra"
    description = ("Removes SHOP_DB_URL from the pipeline's environment. The app refuses "
                   "to start without it -- the classic 'forgotten env var' deploy failure.")

    # The sabotage happens in the environment, not in any file, so apply()
    # edits nothing. The harness reads this list and drops these variables
    # before running Maven (see pipeline.py).
    env_to_remove = ["SHOP_DB_URL"]

    def apply(self, repo_path, params):
        pass

    def revert(self, repo_path):
        pass


class CorruptConfig(Fault):
    name = "CorruptConfig"
    target_class = "infra"
    description = ("Overwrites tax.rate with garbage in application.properties. Config "
                   "parsing blows up with NumberFormatException -- like a bad config "
                   "push breaking a deploy.")

    def apply(self, repo_path, params):
        replace_exact(os.path.join(repo_path, PROPS),
                      "tax.rate=0.08",
                      "tax.rate=not-a-number")

    def revert(self, repo_path):
        replace_exact(os.path.join(repo_path, PROPS),
                      "tax.rate=not-a-number",
                      "tax.rate=0.08")


class KillDatabase(Fault):
    """STUB -- needs Docker. Kept here so the fault library shows the full
    plan; the harness skips stubs instead of crashing on them."""
    name = "KillDatabase"
    target_class = "infra"
    description = "STUB (needs Docker): stops the db container mid-pipeline."

    def apply(self, repo_path, params):
        # TODO(docker): with the compose stack up, run
        #     ["docker", "compose", "stop", "db"]
        # AFTER the pipeline starts, then let the build fail trying to reach
        # the database. Needs a Docker daemon, so this raises until then.
        raise NotImplementedError("KillDatabase needs Docker -- see TODO in infra.py")

    def revert(self, repo_path):
        # TODO(docker): ["docker", "compose", "start", "db"]
        raise NotImplementedError("KillDatabase needs Docker -- see TODO in infra.py")


class NetworkPartition(Fault):
    """STUB -- needs Docker. See KillDatabase above for why it lives here."""
    name = "NetworkPartition"
    target_class = "infra"
    description = "STUB (needs Docker): disconnects the app from the db network."

    def apply(self, repo_path, params):
        # TODO(docker): ["docker", "network", "disconnect", "<project>_default", "<app-container>"]
        # then the build fails on connection timeouts instead of fast errors --
        # a different, realistic infra signature worth having later.
        raise NotImplementedError("NetworkPartition needs Docker -- see TODO in infra.py")

    def revert(self, repo_path):
        # TODO(docker): ["docker", "network", "connect", "<project>_default", "<app-container>"]
        raise NotImplementedError("NetworkPartition needs Docker -- see TODO in infra.py")
