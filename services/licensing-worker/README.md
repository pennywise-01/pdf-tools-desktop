# Licensing Worker (MVP7)

Cloudflare Worker service for payment webhooks and offline license issuance.

## Responsibilities

1. Verify Paddle webhook signatures using `Paddle-Signature` and the endpoint secret.
2. Process transaction events with idempotency guarantees.
3. Issue signed `PTL1` offline license tokens (Ed25519).
4. Provide claim/reissue/revoke APIs for support workflows.
5. Persist events and licenses in Cloudflare D1.

## Data Flow

1. Paddle sends webhook to `POST /webhooks/paddle`.
2. Worker verifies HMAC signature and stores webhook event.
3. Completed payment events produce (or reuse) a Pro license token.
4. License token is persisted and optionally emailed via Resend.
5. Desktop app validates token locally with public key from `src/license_public_keys.json`.

## Setup

### 1) Install dependencies

```bash
cd services/licensing-worker
npm install
```

### 2) Create D1 database and apply migration

```bash
npx wrangler d1 create pdf-tools-licensing
npx wrangler d1 migrations apply pdf-tools-licensing --local
npx wrangler d1 migrations apply pdf-tools-licensing --remote
```

Update `wrangler.toml` with your real `database_id`.

### 3) Configure secrets

```bash
npx wrangler secret put PADDLE_WEBHOOK_SECRET
npx wrangler secret put INTERNAL_API_KEY
npx wrangler secret put LICENSE_SIGNING_KID
npx wrangler secret put LICENSE_SIGNING_PRIVATE_KEY_B64URL
npx wrangler secret put RESEND_API_KEY
npx wrangler secret put RESEND_FROM_EMAIL
```

`RESEND_*` secrets are optional. Paddle can be the primary fulfillment email channel.

### 4) Run locally

```bash
npm run dev
```

### 5) Deploy

```bash
npm run deploy
```

## API Surface

- `GET /health`
- `POST /webhooks/paddle` (Paddle only)
- `POST /api/v1/licenses/issue` (internal API key)
- `POST /api/v1/licenses/claim` (customer/support claim)
- `POST /api/v1/licenses/revoke` (internal API key)
- `GET /api/v1/licenses/:licenseId` (internal API key)

See `openapi.yaml` for request/response details.

## Security Notes

- Webhook route fails closed on invalid signatures.
- Internal endpoints require `x-internal-api-key`.
- Private signing key never leaves the worker.
- Desktop app never needs outbound network for license validation.
- Key rotation is supported via `kid` and multi-key public key file.
