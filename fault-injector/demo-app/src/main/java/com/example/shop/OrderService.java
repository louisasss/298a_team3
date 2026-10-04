package com.example.shop;

// The "business logic" of the demo shop. Thin on purpose: it just wires
// the price calculator and the config together. Real enough to break.
public class OrderService {

    private final PriceCalculator calculator = new PriceCalculator();

    // Total for one order line, including tax.
    public double totalWithTax(Order order) {
        double lineTotal = calculator.lineTotal(order);
        double taxRate = Config.getTaxRate();
        return lineTotal * (1 + taxRate);
    }

    // Health check used by the flaky-test demo. Must answer fast --
    // the pingIsFast test fails the build if this takes over 500 ms.
    public String ping() {
        return "ok";
    }

    // Touches the database config, like a real service would on startup.
    public String dbUrl() {
        return Config.getDbUrl();
    }
}
