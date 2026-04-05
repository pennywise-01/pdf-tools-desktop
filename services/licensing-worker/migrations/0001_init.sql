CREATE TABLE IF NOT EXISTS webhook_events (
  event_id TEXT PRIMARY KEY,
  event_type TEXT NOT NULL,
  status TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  first_received_at TEXT NOT NULL,
  last_received_at TEXT NOT NULL,
  processed_at TEXT,
  error_message TEXT
);

CREATE TABLE IF NOT EXISTS licenses (
  license_id TEXT PRIMARY KEY,
  order_id TEXT NOT NULL UNIQUE,
  customer_id TEXT,
  customer_email TEXT,
  customer_ref_hash TEXT,
  tier TEXT NOT NULL,
  key_id TEXT NOT NULL,
  major_version_max INTEGER NOT NULL,
  features_json TEXT,
  issued_at TEXT NOT NULL,
  not_before TEXT,
  expires_at TEXT,
  revoked_at TEXT,
  revoked_reason TEXT,
  token TEXT NOT NULL,
  last_email_sent_at TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_licenses_customer_email ON licenses(customer_email);
CREATE INDEX IF NOT EXISTS idx_licenses_customer_id ON licenses(customer_id);
