export interface Env {
  LICENSING_DB: D1Database;
  PADDLE_WEBHOOK_SECRET: string;
  INTERNAL_API_KEY: string;
  LICENSE_SIGNING_PRIVATE_KEY_B64URL: string;
  LICENSE_SIGNING_KID: string;
  PADDLE_API_KEY?: string;
  PADDLE_API_BASE_URL?: string;
  LICENSE_DEFAULT_MAJOR_VERSION_MAX?: string;
  RESEND_API_KEY?: string;
  RESEND_FROM_EMAIL?: string;
}

export interface PaddleWebhookEvent {
  event_id: string;
  event_type: string;
  occurred_at?: string;
  data: Record<string, unknown>;
}

export interface LicenseClaims {
  kid: string;
  tier: "pro";
  license_id: string;
  major_version_max: number;
  issued_at: string;
  not_before?: string;
  expires_at?: string;
  customer_ref_hash?: string;
  order_id?: string;
  features?: string[];
}

export interface StoredLicense {
  license_id: string;
  order_id: string;
  customer_id?: string;
  customer_email?: string;
  customer_ref_hash?: string;
  tier: string;
  key_id: string;
  major_version_max: number;
  features?: string[];
  issued_at: string;
  not_before?: string;
  expires_at?: string;
  revoked_at?: string;
  revoked_reason?: string;
  token: string;
  last_email_sent_at?: string;
  created_at: string;
  updated_at: string;
}

export interface IssueLicenseInput {
  orderId: string;
  customerId?: string;
  customerEmail?: string;
  tier?: "pro";
  majorVersionMax?: number;
  notBefore?: string;
  expiresAt?: string;
  features?: string[];
}
