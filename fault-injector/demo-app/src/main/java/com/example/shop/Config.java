package com.example.shop;

import java.io.IOException;
import java.io.InputStream;
import java.util.Properties;

// Reads the settings the app needs, from two different places on purpose:
//   - SHOP_DB_URL comes from the environment, like a real deployed app.
//   - tax.rate comes from application.properties on the classpath.
// A missing or broken setting is a startup/config failure (infra class),
// not a code bug -- which is exactly why the infra faults target this file.
public class Config {

    public static String getDbUrl() {
        String url = System.getenv("SHOP_DB_URL");
        if (url == null || url.isEmpty()) {
            throw new IllegalStateException("SHOP_DB_URL is not set");
        }
        return url;
    }

    public static double getTaxRate() {
        Properties props = new Properties();
        try (InputStream in = Config.class.getResourceAsStream("/application.properties")) {
            if (in == null) {
                throw new IllegalStateException("application.properties is missing from the classpath");
            }
            props.load(in);
        } catch (IOException e) {
            throw new IllegalStateException("could not read application.properties", e);
        }
        String raw = props.getProperty("tax.rate");
        if (raw == null) {
            throw new IllegalStateException("tax.rate is missing from application.properties");
        }
        // Throws NumberFormatException on garbage -- the CorruptConfig fault
        // relies on exactly this.
        return Double.parseDouble(raw);
    }
}
