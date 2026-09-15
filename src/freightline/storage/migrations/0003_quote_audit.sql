-- 0003: quote audit trail, so we can explain a price after the fact.
CREATE TABLE IF NOT EXISTS quote_audit (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    shipment_id   TEXT REFERENCES shipments (id) ON DELETE SET NULL,
    carrier_code  TEXT NOT NULL,
    service       TEXT NOT NULL,
    zone          INTEGER NOT NULL,
    billable_kg   TEXT NOT NULL,
    breakdown     TEXT NOT NULL,
    total_cents   INTEGER NOT NULL,
    currency      TEXT NOT NULL DEFAULT 'USD',
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_quote_audit_carrier ON quote_audit (carrier_code, created_at);
