CREATE TABLE IF NOT EXISTS notification_logs (
    id BIGSERIAL PRIMARY KEY,

    event_id UUID NOT NULL UNIQUE,

    transaction_id UUID NOT NULL,

    customer_id UUID NOT NULL,

    notification_type VARCHAR(50) NOT NULL,

    channel VARCHAR(50) NOT NULL,

    priority VARCHAR(20) NOT NULL,

    risk_level VARCHAR(32) NOT NULL,

    title VARCHAR(255) NOT NULL,

    message VARCHAR(1000) NOT NULL,

    status VARCHAR(30) NOT NULL,

    risk_score INTEGER NOT NULL,

    reasons JSONB NOT NULL DEFAULT '[]'::jsonb,

    ml_prediction VARCHAR(32),

    ml_probability DOUBLE PRECISION,

    ml_risk_level VARCHAR(32),

    ml_model_version VARCHAR(64),

    occurred_at TIMESTAMP WITH TIME ZONE NOT NULL,

    created_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE INDEX IF NOT EXISTS
    ix_notification_logs_event_id
    ON notification_logs(event_id);

CREATE INDEX IF NOT EXISTS
    ix_notification_logs_transaction_id
    ON notification_logs(transaction_id);

CREATE INDEX IF NOT EXISTS
    ix_notification_logs_customer_id
    ON notification_logs(customer_id);

CREATE INDEX IF NOT EXISTS
    ix_notification_logs_notification_type
    ON notification_logs(notification_type);

CREATE INDEX IF NOT EXISTS
    ix_notification_logs_priority
    ON notification_logs(priority);

CREATE INDEX IF NOT EXISTS
    ix_notification_logs_risk_level
    ON notification_logs(risk_level);

CREATE INDEX IF NOT EXISTS
    ix_notification_logs_status
    ON notification_logs(status);

CREATE INDEX IF NOT EXISTS
    ix_notification_customer_created
    ON notification_logs(customer_id, created_at);

CREATE INDEX IF NOT EXISTS
    ix_notification_priority_created
    ON notification_logs(priority, created_at);