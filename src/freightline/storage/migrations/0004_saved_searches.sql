-- 0004: reusable shipment filters for the ops dashboard.
CREATE TABLE IF NOT EXISTS saved_searches (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    name              TEXT NOT NULL,
    filter_expression TEXT NOT NULL,
    order_by          TEXT NOT NULL DEFAULT 'created_at DESC',
    owner             TEXT NOT NULL,
    created_at        TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_saved_searches_owner ON saved_searches (owner);
