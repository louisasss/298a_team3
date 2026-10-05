# Regression faults: the application code itself is wrong.
# Every one of these makes at least one test fail on EVERY run --".
#
# All three are careful text edits on PriceCalculator.java (see base.py's
# replace_exact for why exact-match editing is used instead of anything fancy).

import os
from .base import Fault, replace_exact

PRICE_CALC = os.path.join("src", "main", "java", "com", "example", "shop",
                          "PriceCalculator.java")


class FlipConditional(Fault):
    name = "FlipConditional"
    target_class = "regression"
    description = ("Changes 'quantity >= 10' to 'quantity > 10': the bulk discount "
                   "now skips orders of exactly 10. Breaks bulkDiscountAppliesAtExactlyTen.")

    def apply(self, repo_path, params):
        replace_exact(os.path.join(repo_path, PRICE_CALC),
                      "if (quantity >= 10) {",
                      "if (quantity > 10) {")

    def revert(self, repo_path):
        replace_exact(os.path.join(repo_path, PRICE_CALC),
                      "if (quantity > 10) {",
                      "if (quantity >= 10) {")


class OffByOne(Fault):
    name = "OffByOne"
    target_class = "regression"
    description = ("Changes the basketTotal loop bound from '<' to '<=': the loop reads "
                   "one past the end of the list. Breaks basketTotalAddsLines with "
                   "IndexOutOfBoundsException.")

    def apply(self, repo_path, params):
        replace_exact(os.path.join(repo_path, PRICE_CALC),
                      "for (int i = 0; i < lineTotals.size(); i++) {",
                      "for (int i = 0; i <= lineTotals.size(); i++) {")

    def revert(self, repo_path):
        replace_exact(os.path.join(repo_path, PRICE_CALC),
                      "for (int i = 0; i <= lineTotals.size(); i++) {",
                      "for (int i = 0; i < lineTotals.size(); i++) {")


class NullReturn(Fault):
    name = "NullReturn"
    target_class = "regression"
    description = ("Makes discountFor() return null, breaking its never-null contract. "
                   "The caller auto-unboxes it and every lineTotal test dies with "
                   "NullPointerException.")

    def apply(self, repo_path, params):
        replace_exact(os.path.join(repo_path, PRICE_CALC),
                      "        return discount;",
                      "        return null; // FAULT: broken contract, was 'return discount;'")

    def revert(self, repo_path):
        replace_exact(os.path.join(repo_path, PRICE_CALC),
                      "        return null; // FAULT: broken contract, was 'return discount;'",
                      "        return discount;")
