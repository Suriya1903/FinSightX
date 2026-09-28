-- ============================================================
-- FinSightX Data Warehouse Schema
-- ============================================================

CREATE SCHEMA IF NOT EXISTS analytics;


-- ============================================================
-- Date Dimension
-- ============================================================

CREATE TABLE IF NOT EXISTS analytics.dim_date (
    date_key INTEGER PRIMARY KEY,
    full_date DATE NOT NULL UNIQUE,
    day_number INTEGER NOT NULL,
    month_number INTEGER NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    quarter_number INTEGER NOT NULL,
    year_number INTEGER NOT NULL,
    day_of_week_number INTEGER NOT NULL,
    day_of_week_name VARCHAR(20) NOT NULL,
    is_weekend BOOLEAN NOT NULL
);


-- ============================================================
-- Customer Dimension
-- ============================================================

CREATE TABLE IF NOT EXISTS analytics.dim_customer (
    customer_key BIGSERIAL PRIMARY KEY,
    customer_id UUID NOT NULL UNIQUE,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(255) NOT NULL,
    country VARCHAR(100),
    status VARCHAR(30),
    source_created_at TIMESTAMPTZ,
    source_updated_at TIMESTAMPTZ,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- Merchant Dimension
-- ============================================================

CREATE TABLE IF NOT EXISTS analytics.dim_merchant (
    merchant_key BIGSERIAL PRIMARY KEY,
    merchant_name VARCHAR(200) NOT NULL,
    merchant_category VARCHAR(100),
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (merchant_name, merchant_category)
);


-- ============================================================
-- Device Dimension
-- ============================================================

CREATE TABLE IF NOT EXISTS analytics.dim_device (
    device_key BIGSERIAL PRIMARY KEY,
    device_id VARCHAR(150) NOT NULL UNIQUE,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- Location Dimension
-- ============================================================

CREATE TABLE IF NOT EXISTS analytics.dim_location (
    location_key BIGSERIAL PRIMARY KEY,
    location_name VARCHAR(200) NOT NULL UNIQUE,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- Transaction Fact Table
-- ============================================================

CREATE TABLE IF NOT EXISTS analytics.fact_transactions (
    transaction_key BIGSERIAL PRIMARY KEY,

    transaction_id UUID NOT NULL UNIQUE,

    date_key INTEGER NOT NULL,
    customer_key BIGINT NOT NULL,
    merchant_key BIGINT NOT NULL,
    device_key BIGINT,
    location_key BIGINT,

    amount NUMERIC(18, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL,

    transaction_status VARCHAR(30) NOT NULL,

    risk_level VARCHAR(20),
    risk_score INTEGER,

    transaction_created_at TIMESTAMPTZ NOT NULL,

    loaded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_fact_date
        FOREIGN KEY (date_key)
        REFERENCES analytics.dim_date(date_key),

    CONSTRAINT fk_fact_customer
        FOREIGN KEY (customer_key)
        REFERENCES analytics.dim_customer(customer_key),

    CONSTRAINT fk_fact_merchant
        FOREIGN KEY (merchant_key)
        REFERENCES analytics.dim_merchant(merchant_key),

    CONSTRAINT fk_fact_device
        FOREIGN KEY (device_key)
        REFERENCES analytics.dim_device(device_key),

    CONSTRAINT fk_fact_location
        FOREIGN KEY (location_key)
        REFERENCES analytics.dim_location(location_key)
);


-- ============================================================
-- Analytical Indexes
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_fact_transactions_date
    ON analytics.fact_transactions(date_key);

CREATE INDEX IF NOT EXISTS idx_fact_transactions_customer
    ON analytics.fact_transactions(customer_key);

CREATE INDEX IF NOT EXISTS idx_fact_transactions_merchant
    ON analytics.fact_transactions(merchant_key);

CREATE INDEX IF NOT EXISTS idx_fact_transactions_risk
    ON analytics.fact_transactions(risk_level);

CREATE INDEX IF NOT EXISTS idx_fact_transactions_created_at
    ON analytics.fact_transactions(transaction_created_at);

CREATE INDEX IF NOT EXISTS idx_fact_transactions_status
    ON analytics.fact_transactions(transaction_status);


-- ============================================================
-- ETL Metadata
-- ============================================================

CREATE TABLE IF NOT EXISTS analytics.etl_metadata (
    pipeline_name VARCHAR(100) PRIMARY KEY,
    last_processed_timestamp TIMESTAMPTZ,
    last_run_timestamp TIMESTAMPTZ,
    records_processed BIGINT DEFAULT 0,
    pipeline_status VARCHAR(30),
    error_message TEXT
);