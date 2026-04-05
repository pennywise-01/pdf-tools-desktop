# MVP7 Licensing - Implementation and Go-Live Guide

This document summarizes what is already implemented, what is required to make licensing fully operational in production, and the recommended architecture for hosting and operations.

## 1) Current Implementation Status

### Desktop app (implemented)

- Offline Pro license activation UI is implemented.
- Pro feature gating is implemented in feature navigation flows.
- Signed license verification is implemented locally using Ed25519 public keys.
- Entitlement windows are supported: `not_before`, `expires_at`.
- Optional per-feature entitlements are supported with `features` allowlist claims.
- Activated license is encrypted and stored locally.
- Audit events are recorded for activation failures, invalid stored licenses, and denied Pro access attempts.

Relevant files:

- `src/utils/license_manager.py`
- `src/widgets/license_dialog.py`
- `src/main.py`
- `src/widgets/home_page.py`
- `src/license_public_keys.json`

### License issuance service (implemented scaffold)

- Cloudflare Worker service is implemented with API routes for:
  - Paddle webhooks
  - License issue/reissue
  - License claim
  - License revoke
  - License lookup
- Paddle webhook signature verification is implemented (`Paddle-Signature`, HMAC SHA256 over `ts:rawBody`).
- Event idempotency and processing state are persisted.
- License tokens are signed with Ed25519 private key and stored.
- D1 schema and migration are included.
- Optional fallback email sending via Resend is implemented.
- OpenAPI specification is included.

Relevant files:

- `services/licensing-worker/src/index.ts`
- `services/licensing-worker/src/lib/crypto.ts`
- `services/licensing-worker/src/lib/paddle.ts`
- `services/licensing-worker/src/lib/license.ts`
- `services/licensing-worker/src/lib/db.ts`
- `services/licensing-worker/src/lib/email.ts`
- `services/licensing-worker/migrations/0001_init.sql`
- `services/licensing-worker/openapi.yaml`
- `services/licensing-worker/wrangler.toml`

### Tooling and docs (implemented)

- Key generation tool for signing keypairs.
- Local token issuance tool for testing/support.
- Existing runbook and service docs.

Relevant files:

- `scripts/licensing/generate_license_keys.py`
- `scripts/licensing/issue_license_token.py`
- `docs/licensing/MVP7_LICENSE_RUNBOOK.md`
- `services/licensing-worker/README.md`

## 2) Recommended Production Architecture

Use Cloudflare Workers + D1 for the licensing backend.

Why this stack:

- Low operational overhead.
- Good fit for webhook/API workloads.
- Built-in global edge deployment and TLS.
- Native D1 integration for webhook and license state.
- No always-on VM/server management needed.

### Architecture (logical)

1. User purchases Pro in Paddle checkout.
2. Paddle sends webhook to Worker endpoint (`/webhooks/paddle`).
3. Worker verifies webhook signature.
4. Worker issues or reuses license token and stores in D1.
5. Worker sends token email (optional Resend path) or makes token available through claim flow.
6. User pastes token into desktop app.
7. Desktop app validates token offline using local public key, then enables Pro features.

Key security property:

- Desktop app does not need outbound network calls for license validation after token delivery.

## 3) Required Items to Be Fully Working in Production

## 3.1 Accounts and infrastructure

- Cloudflare account:
  - Worker deployment
  - D1 database
- Paddle account:
  - Product/price setup
  - Webhook notification destination
- Domain/DNS for service endpoint (recommended custom domain)

Optional:

- Resend account for fallback/custom license email sending.

## 3.2 Required secrets and config

Worker secrets (required):

- `PADDLE_WEBHOOK_SECRET`
- `INTERNAL_API_KEY`
- `LICENSE_SIGNING_KID`
- `LICENSE_SIGNING_PRIVATE_KEY_B64URL`

Worker vars:

- `LICENSE_DEFAULT_MAJOR_VERSION_MAX` (default major entitlement)

Optional email secrets:

- `RESEND_API_KEY`
- `RESEND_FROM_EMAIL`

Desktop required key material:

- `src/license_public_keys.json` must contain production public key(s) matching worker signing keys.

## 3.3 Database setup

- Create D1 database.
- Set real `database_id` in `services/licensing-worker/wrangler.toml`.
- Apply migration `services/licensing-worker/migrations/0001_init.sql` to local and remote.

## 3.4 Paddle webhook setup

- Configure webhook destination URL:
  - `https://<your-worker-domain>/webhooks/paddle`
- Subscribe at minimum to events used by service logic:
  - `transaction.completed`
  - `transaction.paid`
  - cancellation/refund event used for revocation flow
- Verify webhook delivery/retry behavior from Paddle dashboard.

## 3.5 Token delivery strategy (email)

Choose one production approach:

1. Paddle fulfillment-first:
- Use Paddle standard purchase email flows.
- Include customer support/claim instructions (order id + claim endpoint).

2. Service email-first (recommended for automatic token delivery):
- Enable Resend secrets.
- Service sends token automatically after successful issuance.

Note:

- Current code supports optional Resend; if not configured, claim/internal flows still work.

## 3.6 Internal operations and support

- Securely store and rotate `INTERNAL_API_KEY`.
- Restrict internal issue/revoke endpoints to trusted systems/users only.
- Define support SOP for:
  - manual reissue
  - claim troubleshooting
  - revocation after refund/chargeback

## 4) Production Go-Live Checklist

1. Generate production signing keypair:
   - `python scripts/licensing/generate_license_keys.py --kid prod-YYYYMMDD`
2. Store private key in Worker secrets only.
3. Commit updated public key in `src/license_public_keys.json`.
4. Create D1 and run migrations.
5. Deploy Worker.
6. Configure Paddle webhook and verify signatures in logs.
7. Configure email path (Resend optional) and test delivery.
8. Test full flow:
   - purchase -> webhook -> issued token -> desktop activation -> Pro unlock
9. Test negative cases:
   - tampered token
   - expired token
   - revoked order
10. Release desktop build containing production public key file.

## 5) Operational and Security Recommendations

- Key rotation:
  - add new `kid`, keep old public keys until old licenses are retired.
- Incident response:
  - if key compromise is suspected, rotate key immediately and reissue active licenses.
- Observability:
  - monitor webhook failures, issuance failures, email send failures, claim/revoke errors.
- Abuse controls (recommended hardening):
  - rate limiting and bot protection for claim endpoint.
  - consider adding signed one-time claim tokens for user-facing self-service portals.

## 6) What Is Not Needed for Runtime Validation

Not required for end-user runtime license checks:

- No always-online license heartbeat.
- No mandatory outbound app network calls for feature unlock.

The app validates signed licenses offline after token delivery.

## 7) Related Project Docs

- `docs/licensing/MVP7_LICENSE_RUNBOOK.md`
- `services/licensing-worker/README.md`
- `services/licensing-worker/openapi.yaml`
- `README.md`
