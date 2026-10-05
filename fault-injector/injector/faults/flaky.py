# Flaky faults: the failure comes and goes between runs on the SAME code.

import os
from .base import Fault, replace_exact

ORDER_SERVICE = os.path.join("src", "main", "java", "com", "example", "shop",
                             "OrderService.java")
PRICE_CALC = os.path.join("src", "main", "java", "com", "example", "shop",
                          "PriceCalculator.java")


class RandomSleep(Fault):
    name = "RandomSleep"
    target_class = "flaky"
    description = ("Inserts a random 0-1000 ms sleep into ping(). The pingIsFast test "
                   "allows only 500 ms, so it fails roughly half the runs and passes "
                   "the rest -- textbook flakiness.")

    def apply(self, repo_path, params):
        replace_exact(os.path.join(repo_path, ORDER_SERVICE),
                      "    public String ping() {\n        return \"ok\";\n    }",
                      "    public String ping() {\n"
                      "        // FAULT (flaky): sleep a random 0-1000 ms. The test\n"
                      "        // allows 500 ms, so this straddles the threshold.\n"
                      "        try {\n"
                      "            Thread.sleep((long) (Math.random() * 1000));\n"
                      "        } catch (InterruptedException e) {\n"
                      "            Thread.currentThread().interrupt();\n"
                      "        }\n"
                      "        return \"ok\";\n"
                      "    }")

    def revert(self, repo_path):
        replace_exact(os.path.join(repo_path, ORDER_SERVICE),
                      "    public String ping() {\n"
                      "        // FAULT (flaky): sleep a random 0-1000 ms. The test\n"
                      "        // allows 500 ms, so this straddles the threshold.\n"
                      "        try {\n"
                      "            Thread.sleep((long) (Math.random() * 1000));\n"
                      "        } catch (InterruptedException e) {\n"
                      "            Thread.currentThread().interrupt();\n"
                      "        }\n"
                      "        return \"ok\";\n"
                      "    }",
                      "    public String ping() {\n        return \"ok\";\n    }")


class RandomFailure(Fault):
    name = "RandomFailure"
    target_class = "flaky"
    description = ("Makes lineTotal() throw on ~50% of calls. Each test calling it "
                   "is a coin flip, so the build fails most runs but sometimes "
                   "goes green -- flaky at the build level.")

    def apply(self, repo_path, params):
        replace_exact(os.path.join(repo_path, PRICE_CALC),
                      "    public double lineTotal(Order order) {\n"
                      "        double subtotal = order.getQuantity() * order.getUnitPrice();",
                      "    public double lineTotal(Order order) {\n"
                      "        // FAULT (flaky): explode on roughly half the calls.\n"
                      "        if (Math.random() < 0.5) {\n"
                      "            throw new RuntimeException(\"simulated flake in lineTotal\");\n"
                      "        }\n"
                      "        double subtotal = order.getQuantity() * order.getUnitPrice();")

    def revert(self, repo_path):
        replace_exact(os.path.join(repo_path, PRICE_CALC),
                      "    public double lineTotal(Order order) {\n"
                      "        // FAULT (flaky): explode on roughly half the calls.\n"
                      "        if (Math.random() < 0.5) {\n"
                      "            throw new RuntimeException(\"simulated flake in lineTotal\");\n"
                      "        }\n"
                      "        double subtotal = order.getQuantity() * order.getUnitPrice();",
                      "    public double lineTotal(Order order) {\n"
                      "        double subtotal = order.getQuantity() * order.getUnitPrice();")
