-- ============================================================
-- HealthGuard AI – PostgreSQL Database Schema
-- Run: psql -U postgres -f schema.sql
-- ============================================================

-- Create database (run as superuser if it does not exist yet)
-- psql -U postgres -c "CREATE DATABASE health_insurance_db;"

\c health_insurance_db

-- ── Users ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    username      VARCHAR(50)  UNIQUE NOT NULL,
    email         VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name     VARCHAR(100),
    role          VARCHAR(10)  NOT NULL DEFAULT 'user'
                      CHECK (role IN ('user', 'admin')),
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users (username);
CREATE INDEX IF NOT EXISTS idx_users_email    ON users (email);

-- ── Predictions ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS predictions (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    age             INTEGER,
    gender          VARCHAR(10),
    bmi             FLOAT,
    children        INTEGER,
    smoker          VARCHAR(5),
    region          VARCHAR(20),
    predicted_price FLOAT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_predictions_user_id   ON predictions (user_id);
CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON predictions (created_at);

-- ── Payments ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS payments (
    id             SERIAL PRIMARY KEY,
    user_id        INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount         FLOAT NOT NULL,
    payment_method VARCHAR(50),
    status         VARCHAR(10) NOT NULL DEFAULT 'pending'
                       CHECK (status IN ('pending', 'completed', 'failed')),
    transaction_id VARCHAR(100),
    plan_type      VARCHAR(50),
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments (user_id);
CREATE INDEX IF NOT EXISTS idx_payments_status  ON payments (status);

-- ── Default Admin Seed ────────────────────────────────────────
-- Password: admin123  (bcrypt hash — app.py also auto-creates this on first run)
INSERT INTO users (username, email, password_hash, full_name, role)
VALUES (
    'admin',
    'admin@healthinsure.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeOziwxGWvTSmrPm.',
    'System Admin',
    'admin'
)
ON CONFLICT (username) DO NOTHING;
