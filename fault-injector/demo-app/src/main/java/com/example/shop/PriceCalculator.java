package com.example.shop;

import java.util.List;

// Adds up order lines and applies a bulk discount.
// Kept deliberately plain: the fault injector edits exact lines in this
// file, so every interesting line is written in the most obvious way.
public class PriceCalculator {

    // Total for one order line: subtotal minus discount.
    public double lineTotal(Order order) {
        double subtotal = order.getQuantity() * order.getUnitPrice();
        // discountFor() promises to never return null, so unboxing here is safe.
        // The NullReturn fault breaks that promise on purpose.
        double discount = discountFor(order);
        return subtotal - discount;
    }

    // Discount for one order line. 10% off when you buy 10 or more.
    // Returns a Double (object, not primitive) so that "returning null"
    // is a meaningful contract violation for the NullReturn fault.
    public Double discountFor(Order order) {
        int quantity = order.getQuantity();
        double subtotal = order.getQuantity() * order.getUnitPrice();
        Double discount = 0.0;
        if (quantity >= 10) {
            discount = subtotal * 0.10;
        }
        return discount;
    }

    // Adds up a list of line totals. Plain indexed loop on purpose --
    // the OffByOne fault targets the loop bound.
    public double basketTotal(List<Double> lineTotals) {
        double total = 0.0;
        for (int i = 0; i < lineTotals.size(); i++) {
            total += lineTotals.get(i);
        }
        return total;
    }
}
