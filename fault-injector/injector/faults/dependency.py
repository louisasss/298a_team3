# Dependency faults: the build can't get what it needs.

import os
from .base import Fault, replace_exact

POM = "pom.xml"


class BumpNonexistentVersion(Fault):
    name = "BumpNonexistentVersion"
    target_class = "dependency"
    description = ("Changes junit 4.13.2 to 99.99.99 in pom.xml. Maven cannot resolve "
                   "it -- like a typo'd or yanked version pin. Fails in dependency "
                   "resolution, before tests.")

    def apply(self, repo_path, params):
        replace_exact(os.path.join(repo_path, POM),
                      "      <artifactId>junit</artifactId>\n      <version>4.13.2</version>",
                      "      <artifactId>junit</artifactId>\n      <version>99.99.99</version>")

    def revert(self, repo_path):
        replace_exact(os.path.join(repo_path, POM),
                      "      <artifactId>junit</artifactId>\n      <version>99.99.99</version>",
                      "      <artifactId>junit</artifactId>\n      <version>4.13.2</version>")


class TypoArtifactId(Fault):
    name = "TypoArtifactId"
    target_class = "dependency"
    description = ("Renames the junit artifactId to junit-typo in pom.xml. Maven looks "
                   "for an artifact that does not exist -- the 'oops, typo in the pom' "
                   "failure everyone has shipped at least once.")

    def apply(self, repo_path, params):
        replace_exact(os.path.join(repo_path, POM),
                      "      <artifactId>junit</artifactId>",
                      "      <artifactId>junit-typo</artifactId>")

    def revert(self, repo_path):
        replace_exact(os.path.join(repo_path, POM),
                      "      <artifactId>junit-typo</artifactId>",
                      "      <artifactId>junit</artifactId>")
