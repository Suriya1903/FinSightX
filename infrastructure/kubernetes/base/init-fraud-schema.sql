-- ==========================================================
-- FinSightX - Fraud Assessment Schema
-- Kubernetes PostgreSQL Initialization
-- ==========================================================

-- Sequence for fraud_assessments.id
CREATE SEQUENCE IF NOT EXISTS fraud_assessments_id_seq;

-- Main fraud assessment table
CREATE TABLE IF NOT EXISTS fraud_assessments (
    id BIGINT NOT NULL DEFAULT nextval('fraud_assessments_id_seq'),

    event_id UUID NOT NULL,

    transaction_id UUID NOT NULL,

    customer_id UUID NOT NULL,

    risk_level VARCHAR(20) NOT NULL,

    risk_score INTEGER NOT NULL,

    reasons JSONB NOT NULL DEFAULT '[]'::jsonb,

    assessed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    ml_prediction VARCHAR(32),

    ml_probability DOUBLE PRECISION,

    ml_risk_level VARCHAR(32),

    ml_model_version VARCHAR(64),

    CONSTRAINT fraud_assessments_pkey
        PRIMARY KEY (id),

    CONSTRAINT fraud_assessments_event_id_key
        UNIQUE (event_id),

    CONSTRAINT fraud_assessments_transaction_id_key
        UNIQUE (transaction_id)
);

-- Make the sequence owned by the table's id column.
ALTER SEQUENCE fraud_assessments_id_seq
OWNED BY fraud_assessments.id;

-- Index for assessment-time queries.
CREATE INDEX IF NOT EXISTS idx_fraud_assessments_assessed_at
    ON fraud_assessments (assessed_at);

-- Index for customer-level fraud analysis.
CREATE INDEX IF NOT EXISTS idx_fraud_assessments_customer
    ON fraud_assessments (customer_id);

-- Index for risk-level filtering.
CREATE INDEX IF NOT EXISTS idx_fraud_assessments_risk
    ON fraud_assessments (risk_level);