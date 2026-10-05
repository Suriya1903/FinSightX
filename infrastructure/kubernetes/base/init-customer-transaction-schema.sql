-- ==========================================================
-- FinSightX - Customer & Transaction Schema
-- Kubernetes PostgreSQL Initialization
-- ==========================================================

-- ==========================================================
-- CUSTOMERS
-- ==========================================================

CREATE TABLE IF NOT EXISTS customers (
    id UUID NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(30),
    country VARCHAR(100),
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,

    CONSTRAINT customers_pkey
        PRIMARY KEY (id),

    CONSTRAINT customers_email_key
        UNIQUE (email)
);

CREATE INDEX IF NOT EXISTS ix_customers_email
    ON customers (email);


-- ==========================================================
-- TRANSACTIONS
-- ==========================================================

CREATE TABLE IF NOT EXISTS transactions (
    id UUID NOT NULL,
    customer_id UUID NOT NULL,
    amount NUMERIC(18,2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    merchant_name VARCHAR(200) NOT NULL,
    merchant_category VARCHAR(100),
    location VARCHAR(200),
    device_id VARCHAR(150),
    status VARCHAR(30) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,

    CONSTRAINT transactions_pkey
        PRIMARY KEY (id),

    CONSTRAINT transactions_customer_id_fkey
        FOREIGN KEY (customer_id)
        REFERENCES customers(id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_transactions_created_at
    ON transactions (created_at);

CREATE INDEX IF NOT EXISTS ix_transactions_customer_id
    ON transactions (customer_id);

CREATE INDEX IF NOT EXISTS ix_transactions_customer_created_at
    ON transactions (customer_id, created_at);