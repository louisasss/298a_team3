package com.example.shop;

// One line on a customer order: what was bought, how many, at what price.
public class Order {
    private final String itemName;
    private final int quantity;
    private final double unitPrice;

    public Order(String itemName, int quantity, double unitPrice) {
        this.itemName = itemName;
        this.quantity = quantity;
        this.unitPrice = unitPrice;
    }

    public String getItemName() {
        return itemName;
    }

    public int getQuantity() {
        return quantity;
    }

    public double getUnitPrice() {
        return unitPrice;
    }
}
