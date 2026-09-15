-- 0001: shipments and their canonical status.
CREATE TABLE IF NOT EXISTS shipments (
    id                      TEXT PRIMARY KEY,
    carrier_code            TEXT NOT NULL,
    service                 TEXT NOT NULL,
    tracking_number         TEXT NOT NULL UNIQUE,
    origin_postal_code      TEXT NOT NULL,
    destination_postal_code TEXT NOT NULL,
    status                  TEXT NOT NULL DEFAULT 'created',
    total_cents             INTEGER NOT NULL DEFAULT 0,
    currency                TEXT NOT NULL DEFAULT 'USD',
    reference               TEXT,
    created_at              TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_shipments_carrier ON shipments (carrier_code);
CREATE INDEX IF NOT EXISTS idx_shipments_status ON shipments (status);
CREATE INDEX IF NOT EXISTS idx_shipments_reference ON shipments (reference);
