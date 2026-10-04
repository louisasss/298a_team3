package com.example.shop;

import java.util.Arrays;
import org.junit.Test;
import static org.junit.Assert.*;

// The test suite the injector tries to break. Each test pins down one
// behavior, and each fault in the library is aimed at breaking specific
// tests below (the comments say which). JUnit 4 on purpose: simpler
// annotations, less to explain to a teammate.
public class OrderServiceTest {

    private final OrderService service = new OrderService();
    private final PriceCalculator calc = new PriceCalculator();

    @Test
    public void lineTotalWithoutDiscount() {
        Order order = new Order("book", 2, 10.0);
        assertEquals(20.0, calc.lineTotal(order), 0.001);
    }

    @Test
    public void bulkDiscountAppliesAtExactlyTen() {
        Order order = new Order("book", 10, 10.0);
        // 100 minus 10% = 90. The FlipConditional fault breaks exactly
        // this boundary (it changes >= to >, so 10 no longer qualifies).
        assertEquals(90.0, calc.lineTotal(order), 0.001);
    }

    @Test
    public void basketTotalAddsLines() {
        // The OffByOne fault makes this throw IndexOutOfBoundsException.
        assertEquals(60.0, calc.basketTotal(Arrays.asList(20.0, 40.0)), 0.001);
    }

    @Test
    public void totalIncludesTax() {
        Order order = new Order("book", 1, 100.0);
        // tax.rate=0.08 in application.properties, so 100 -> 108.
        // The CorruptConfig fault breaks this by garbage-ing the tax rate.
        assertEquals(108.0, service.totalWithTax(order), 0.001);
    }

    @Test
    public void dbUrlIsConfigured() {
        // Needs SHOP_DB_URL in the environment (pipeline.py sets a default).
        // The DeleteEnvVar fault removes it and this test errors out.
        assertFalse(service.dbUrl().isEmpty());
    }

    @Test(timeout = 500)
    public void pingIsFast() {
        // Must answer within 500 ms. The RandomSleep flaky fault inserts a
        // random 0-1000 ms pause, so this fails about half the runs.
        assertEquals("ok", service.ping());
    }
}
