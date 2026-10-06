# Regression faults: the application code itself is wrong.
# Every one of these makes at least one test fail on EVERY run --".
#
# All three are careful text edits on PriceCalculator.java (see base.py's
# replace_exact for why exact-match editing is used instead of anything fancy).

import os
from .base import Fault, replace_exact

PRICE_CALC = os.path.join("src", "main", "java", "com", "example", "shop",
                          "PriceCalculator.java")

ORDER_SERVICE = os.path.join("src", "main", "java", "com", "example", "shop",
                             "OrderService.java")
ORDER = os.path.join("src", "main", "java", "com", "example", "shop",
                     "Order.java")

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


class DropImport(Fault):
    name = "DropImport"
    target_class = "regression"
    description = ("Deletes 'import java.util.List;' from PriceCalculator.java: the code "
                   "no longer compiles ('cannot find symbol'). Breaks the build at the "
                   "compile stage, before any test runs.")

    def apply(self, repo_path, params):
        replace_exact(os.path.join(repo_path, PRICE_CALC),
                      "import java.util.List;\n\n// Adds up order lines and applies a bulk discount.",
                      "// Adds up order lines and applies a bulk discount.")

    def revert(self, repo_path):
        replace_exact(os.path.join(repo_path, PRICE_CALC),
                      "// Adds up order lines and applies a bulk discount.",
                      "import java.util.List;\n\n// Adds up order lines and applies a bulk discount.")


class AddInsteadOfMultiply(Fault):
    name = "AddInsteadOfMultiply"
    target_class = "regression"
    description = ("Changes '*' to '+' in lineTotal()'s subtotal: 2 books at 10.0 "
                   "now total 12.0 instead of 20.0. Breaks lineTotalWithoutDiscount.")

    def apply(self, repo_path, params):
        replace_exact(os.path.join(repo_path, PRICE_CALC),
                      "    public double lineTotal(Order order) {\n"
                      "        double subtotal = order.getQuantity() * order.getUnitPrice();",
                      "    public double lineTotal(Order order) {\n"
                      "        double subtotal = order.getQuantity() + order.getUnitPrice();")

    def revert(self, repo_path):
        replace_exact(os.path.join(repo_path, PRICE_CALC),
                      "    public double lineTotal(Order order) {\n"
                      "        double subtotal = order.getQuantity() + order.getUnitPrice();",
                      "    public double lineTotal(Order order) {\n"
                      "        double subtotal = order.getQuantity() * order.getUnitPrice();")


class BreakTaxFormula(Fault):
    name = "BreakTaxFormula"
    target_class = "regression"
    description = ("Drops the '(1 + ...)' in totalWithTax(): tax becomes a plain multiplier. "
                   "100.0 at 8% tax comes out 8.0 instead of 108.0. Breaks totalIncludesTax.")

    def apply(self, repo_path, params):
        replace_exact(os.path.join(repo_path, ORDER_SERVICE),
                      "return lineTotal * (1 + taxRate);",
                      "return lineTotal * taxRate;")

    def revert(self, repo_path):
        replace_exact(os.path.join(repo_path, ORDER_SERVICE),
                      "return lineTotal * taxRate;",
                      "return lineTotal * (1 + taxRate);")


class NegateBasketSum(Fault):
    name = "NegateBasketSum"
    target_class = "regression"
    description = ("Changes '+=' to '-=' in basketTotal()'s loop: the basket total comes out "
                   "negative. Breaks basketTotalAddsLines with an assertion failure "
                   "(OffByOne breaks the same test with an exception instead).")

    def apply(self, repo_path, params):
        replace_exact(os.path.join(repo_path, PRICE_CALC),
                      "total += lineTotals.get(i);",
                      "total -= lineTotals.get(i);")

    def revert(self, repo_path):
        replace_exact(os.path.join(repo_path, PRICE_CALC),
                      "total -= lineTotals.get(i);",
                      "total += lineTotals.get(i);")


class WrongQuantity(Fault):
    name = "WrongQuantity"
    target_class = "regression"
    description = ("Makes Order.getQuantity() return quantity + 1: every order looks one unit "
                   "bigger than it is. Breaks lineTotalWithoutDiscount and the discount tests.")

    def apply(self, repo_path, params):
        replace_exact(os.path.join(repo_path, ORDER),
                      "    public int getQuantity() {\n"
                      "        return quantity;\n"
                      "    }",
                      "    public int getQuantity() {\n"
                      "        return quantity + 1;\n"
                      "    }")

    def revert(self, repo_path):
        replace_exact(os.path.join(repo_path, ORDER),
                      "    public int getQuantity() {\n"
                      "        return quantity + 1;\n"
                      "    }",
                      "    public int getQuantity() {\n"
                      "        return quantity;\n"
                      "    }")
