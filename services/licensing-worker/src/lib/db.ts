import { StoredLicense } from "../types";

interface LicenseRow {
  license_id: string;
  order_id: string;
  customer_id: string | null;
  customer_email: string | null;
  customer_ref_hash: string | null;
  tier: string;
  key_id: string;
  major_version_max: number;
  features_json: string | null;
  issued_at: string;
  not_before: string | null;
  expires_at: string | null;
  revoked_at: string | null;
  revoked_reason: string | null;
  token: string;
  last_email_sent_at: string | null;
  created_at: string;
  updated_at: string;
}

function toStoredLicense(row: LicenseRow): StoredLicense {
  let features: string[] | undefined;
  if (row.features_json) {
    try {
      const parsed = JSON.parse(row.features_json);
      if (Array.isArray(parsed)) {
        features = parsed.filter((item): item is string => typeof item === "string");
      }
    } catch {
      features = undefined;
    }
  }

  return {
    license_id: row.license_id,
    order_id: row.order_id,
    customer_id: row.customer_id ?? undefined,
    customer_email: row.customer_email ?? undefined,
    customer_ref_hash: row.customer_ref_hash ?? undefined,
    tier: row.tier,
    key_id: row.key_id,
    major_version_max: row.major_version_max,
    features,
    issued_at: row.issued_at,
    not_before: row.not_before ?? undefined,
    expires_at: row.expires_at ?? undefined,
    revoked_at: row.revoked_at ?? undefined,
    revoked_reason: row.revoked_reason ?? undefined,
    token: row.token,
    last_email_sent_at: row.last_email_sent_at ?? undefined,
    created_at: row.created_at,
    updated_at: row.updated_at,
  };
}

export async function hasProcessedWebhookEvent(db: D1Database, eventId: string): Promise<boolean> {
  const row = await db
    .prepare(
      "SELECT event_id FROM webhook_events WHERE event_id = ?1 AND status = 'processed' LIMIT 1",
    )
    .bind(eventId)
    .first<{ event_id: string }>();
  return !!row;
}

export async function recordWebhookEvent(
  db: D1Database,
  args: {
    eventId: string;
    eventType: string;
    payloadJson: string;
    nowIso: string;
  },
): Promise<void> {
  await db
    .prepare(
      `INSERT INTO webhook_events (event_id, event_type, status, payload_json, first_received_at, last_received_at)
       VALUES (?1, ?2, 'received', ?3, ?4, ?4)
       ON CONFLICT(event_id) DO UPDATE SET
         event_type = excluded.event_type,
         payload_json = excluded.payload_json,
         last_received_at = excluded.last_received_at`,
    )
    .bind(args.eventId, args.eventType, args.payloadJson, args.nowIso)
    .run();
}

export async function markWebhookProcessed(
  db: D1Database,
  args: { eventId: string; nowIso: string },
): Promise<void> {
  await db
    .prepare(
      `UPDATE webhook_events
       SET status = 'processed', processed_at = ?2, error_message = NULL
       WHERE event_id = ?1`,
    )
    .bind(args.eventId, args.nowIso)
    .run();
}

export async function markWebhookFailed(
  db: D1Database,
  args: { eventId: string; nowIso: string; errorMessage: string },
): Promise<void> {
  await db
    .prepare(
      `UPDATE webhook_events
       SET status = 'failed', processed_at = ?2, error_message = ?3
       WHERE event_id = ?1`,
    )
    .bind(args.eventId, args.nowIso, args.errorMessage.slice(0, 1500))
    .run();
}

export async function getLicenseByOrderId(
  db: D1Database,
  orderId: string,
): Promise<StoredLicense | null> {
  const row = await db
    .prepare("SELECT * FROM licenses WHERE order_id = ?1 LIMIT 1")
    .bind(orderId)
    .first<LicenseRow>();

  return row ? toStoredLicense(row) : null;
}

export async function getLicenseByLicenseId(
  db: D1Database,
  licenseId: string,
): Promise<StoredLicense | null> {
  const row = await db
    .prepare("SELECT * FROM licenses WHERE license_id = ?1 LIMIT 1")
    .bind(licenseId)
    .first<LicenseRow>();

  return row ? toStoredLicense(row) : null;
}

export async function upsertLicense(
  db: D1Database,
  record: StoredLicense,
): Promise<void> {
  await db
    .prepare(
      `INSERT INTO licenses (
         license_id,
         order_id,
         customer_id,
         customer_email,
         customer_ref_hash,
         tier,
         key_id,
         major_version_max,
         features_json,
         issued_at,
         not_before,
         expires_at,
         revoked_at,
         revoked_reason,
         token,
         last_email_sent_at,
         created_at,
         updated_at
       ) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12, ?13, ?14, ?15, ?16, ?17, ?18)
       ON CONFLICT(order_id) DO UPDATE SET
         customer_id = excluded.customer_id,
         customer_email = excluded.customer_email,
         customer_ref_hash = excluded.customer_ref_hash,
         tier = excluded.tier,
         key_id = excluded.key_id,
         major_version_max = excluded.major_version_max,
         features_json = excluded.features_json,
         issued_at = excluded.issued_at,
         not_before = excluded.not_before,
         expires_at = excluded.expires_at,
         revoked_at = excluded.revoked_at,
         revoked_reason = excluded.revoked_reason,
         token = excluded.token,
         last_email_sent_at = excluded.last_email_sent_at,
         updated_at = excluded.updated_at`,
    )
    .bind(
      record.license_id,
      record.order_id,
      record.customer_id ?? null,
      record.customer_email ?? null,
      record.customer_ref_hash ?? null,
      record.tier,
      record.key_id,
      record.major_version_max,
      record.features ? JSON.stringify(record.features) : null,
      record.issued_at,
      record.not_before ?? null,
      record.expires_at ?? null,
      record.revoked_at ?? null,
      record.revoked_reason ?? null,
      record.token,
      record.last_email_sent_at ?? null,
      record.created_at,
      record.updated_at,
    )
    .run();
}

export async function revokeLicenseByOrderId(
  db: D1Database,
  args: { orderId: string; reason: string; nowIso: string },
): Promise<number> {
  const result = await db
    .prepare(
      `UPDATE licenses
       SET revoked_at = ?2, revoked_reason = ?3, updated_at = ?2
       WHERE order_id = ?1 AND revoked_at IS NULL`,
    )
    .bind(args.orderId, args.nowIso, args.reason.slice(0, 500))
    .run();

  return result.success ? result.meta.changes : 0;
}

export async function setLicenseEmailSent(
  db: D1Database,
  args: { orderId: string; nowIso: string },
): Promise<void> {
  await db
    .prepare(
      `UPDATE licenses
       SET last_email_sent_at = ?2, updated_at = ?2
       WHERE order_id = ?1`,
    )
    .bind(args.orderId, args.nowIso)
    .run();
}
