BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Users
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('student', 'faculty', 'admin')),
    department TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Leave requests
CREATE TABLE IF NOT EXISTS leave_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    leave_type TEXT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    days_requested INT GENERATED ALWAYS AS ((end_date - start_date + 1)) STORED,
    reason TEXT,
    status TEXT NOT NULL DEFAULT 'PENDING'
        CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED', 'PROCESSING')),
    decision_source TEXT
        CHECK (decision_source IN ('rule_engine', 'ai', 'admin')),
    ai_reasoning TEXT,
    idempotency_key TEXT UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_leave_dates_valid CHECK (end_date >= start_date)
);

-- Audit logs (append-only)
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type TEXT NOT NULL,
    entity_id UUID NOT NULL,
    actor_id UUID REFERENCES users(id),
    actor_type TEXT,
    action TEXT NOT NULL,
    prev_state JSONB,
    new_state JSONB,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Configurable leave rules
CREATE TABLE IF NOT EXISTS leave_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_key TEXT UNIQUE NOT NULL,
    rule_value JSONB NOT NULL,
    description TEXT,
    priority INT NOT NULL DEFAULT 100,
    is_active BOOLEAN NOT NULL DEFAULT true,
    updated_by UUID REFERENCES users(id),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Leave balances (per user per year)
CREATE TABLE IF NOT EXISTS leave_balances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    leave_type TEXT NOT NULL,
    year INT NOT NULL,
    total INT NOT NULL CHECK (total >= 0),
    used INT NOT NULL DEFAULT 0 CHECK (used >= 0),
    UNIQUE (user_id, leave_type, year)
);

-- Indexes from HLD
CREATE INDEX IF NOT EXISTS idx_lr_user_id ON leave_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_lr_status ON leave_requests(status);
CREATE INDEX IF NOT EXISTS idx_lr_created_at ON leave_requests(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_lr_user_date ON leave_requests(user_id, start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_al_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_lb_user_year ON leave_balances(user_id, year);
-- users.email unique index is created via UNIQUE constraint

COMMIT;
