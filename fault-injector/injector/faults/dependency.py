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


class TypoGroupId(Fault):
    name = "TypoGroupId"
    target_class = "dependency"
    description = ("Renames the junit groupId to junit-typo in pom.xml. Maven looks for "
                   "an artifact under a group that does not exist -- same family as "
                   "TypoArtifactId, wrong coordinate.")

    def apply(self, repo_path, params):
        replace_exact(os.path.join(repo_path, POM),
                      "      <groupId>junit</groupId>",
                      "      <groupId>junit-typo</groupId>")

    def revert(self, repo_path):
        replace_exact(os.path.join(repo_path, POM),
                      "      <groupId>junit-typo</groupId>",
                      "      <groupId>junit</groupId>")


class RemoveDependency(Fault):
    name = "RemoveDependency"
    target_class = "dependency"
    description = ("Deletes the whole junit dependency block from pom.xml. Resolution "
                   "succeeds (nothing to resolve) but compilation fails with "
                   "'package org.junit does not exist' -- the 'deleted a dependency "
                   "that was still used' failure.")

    def apply(self, repo_path, params):
        replace_exact(os.path.join(repo_path, POM),
                      "    <dependency>\n"
                      "      <groupId>junit</groupId>\n"
                      "      <artifactId>junit</artifactId>\n"
                      "      <version>4.13.2</version>\n"
                      "      <scope>test</scope>\n"
                      "    </dependency>",
                      "    <!-- FAULT: junit dependency removed -->")

    def revert(self, repo_path):
        replace_exact(os.path.join(repo_path, POM),
                      "    <!-- FAULT: junit dependency removed -->",
                      "    <dependency>\n"
                      "      <groupId>junit</groupId>\n"
                      "      <artifactId>junit</artifactId>\n"
                      "      <version>4.13.2</version>\n"
                      "      <scope>test</scope>\n"
                      "    </dependency>")


class CorruptPomXml(Fault):
    name = "CorruptPomXml"
    target_class = "dependency"
    description = ("Truncates the </dependencies> closing tag in pom.xml. Maven cannot "
                   "even parse the build file ('Non-parseable POM') -- dies before "
                   "dependency resolution starts.")

    def apply(self, repo_path, params):
        replace_exact(os.path.join(repo_path, POM),
                      "  </dependencies>",
                      "  </dependencie>")

    def revert(self, repo_path):
        replace_exact(os.path.join(repo_path, POM),
                      "  </dependencie>",
                      "  </dependencies>")
