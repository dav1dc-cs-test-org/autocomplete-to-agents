-- 0002: append-only tracking scan history.
CREATE TABLE IF NOT EXISTS tracking_events (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    shipment_id         TEXT NOT NULL REFERENCES shipments (id) ON DELETE CASCADE,
    carrier_code        TEXT NOT NULL,
    carrier_status_code TEXT NOT NULL,
    status              TEXT NOT NULL,
    description         TEXT NOT NULL,
    location            TEXT,
    occurred_at         TEXT NOT NULL,
    recorded_at         TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_events_shipment ON tracking_events (shipment_id, occurred_at);
