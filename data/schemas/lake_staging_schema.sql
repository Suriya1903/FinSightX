CREATE SCHEMA IF NOT EXISTS analytics;


CREATE TABLE IF NOT EXISTS analytics.stg_processed_transactions (
    transaction_id UUID,
    customer_id UUID,
    amount NUMERIC(18, 2),
    currency VARCHAR(3),

    merchant_name VARCHAR(200),
    merchant_category VARCHAR(100),

    location VARCHAR(200),
    device_id VARCHAR(150),

    event_type VARCHAR(100),
    event_version VARCHAR(50),
    event_id UUID,

    occurred_at TIMESTAMPTZ,
    transaction_date DATE,

    transaction_year INTEGER,
    transaction_month INTEGER,
    transaction_day INTEGER,

    amount_band VARCHAR(30),
    data_quality_status VARCHAR(30),
    processing_layer VARCHAR(30),

    loaded_at TIMESTAMP
);


CREATE INDEX IF NOT EXISTS
idx_stg_processed_transaction_id
ON analytics.stg_processed_transactions(
    transaction_id
);


CREATE INDEX IF NOT EXISTS
idx_stg_processed_customer_id
ON analytics.stg_processed_transactions(
    customer_id
);


CREATE INDEX IF NOT EXISTS
idx_stg_processed_date
ON analytics.stg_processed_transactions(
    transaction_date
);