# The full fault library in one place.
#
# The harness imports ALL_FAULTS and never needs to know which file a fault
# lives in. To add a new fault:
#   1. Write its class in the right file below (regression.py, flaky.py,
#      infra.py, or dependency.py) -- copy the nearest existing fault.
#   2. Add it to the ALL_FAULTS list at the bottom.
# That's it. Nothing else changes.

from .regression import FlipConditional, OffByOne, NullReturn, DropImport, AddInsteadOfMultiply, BreakTaxFormula, NegateBasketSum, WrongQuantity
from .flaky import RandomSleep, RandomFailure, FlakyPingValue, FlakyDbConnection
from .infra import DeleteEnvVar, CorruptConfig, MissingTaxRate, BadJavaVersion, KillDatabase, NetworkPartition
from .dependency import BumpNonexistentVersion, TypoArtifactId, TypoGroupId, RemoveDependency, CorruptPomXml

ALL_FAULTS = [
    # Regression: the code is wrong, tests fail every time.
    FlipConditional(),
    OffByOne(),
    NullReturn(),
    DropImport(),
    AddInsteadOfMultiply(),
    BreakTaxFormula(),
    NegateBasketSum(),
    WrongQuantity(),
    # Flaky: the failure comes and goes between runs.
    RandomSleep(),
    RandomFailure(),
    FlakyPingValue(),
    FlakyDbConnection(),
    # Infra: the environment is broken, not the code.
    DeleteEnvVar(),
    CorruptConfig(),
    MissingTaxRate(),
    BadJavaVersion(),
    KillDatabase(),      # stub -- needs Docker
    NetworkPartition(),  # stub -- needs Docker
    # Dependency: the build can't get what it needs.
    BumpNonexistentVersion(),
    TypoArtifactId(),
    TypoGroupId(),
    RemoveDependency(),
    CorruptPomXml()
]
