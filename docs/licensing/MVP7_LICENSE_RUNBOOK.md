# MVP7 License Runbook

This runbook covers production operation of offline license issuance and validation.

## 1) Key Management

1. Generate key material:
   - `python scripts/licensing/generate_license_keys.py --kid prod-YYYYMMDD`
2. Commit only public keys in `src/license_public_keys.json`.
3. Store private key securely and set worker secrets:
   - `LICENSE_SIGNING_KID`
   - `LICENSE_SIGNING_PRIVATE_KEY_B64URL`
4. Rotate keys by adding a new `kid` entry. Keep old public keys until old licenses are no longer needed.

## 2) Paddle Webhook Setup

1. Configure notification destination URL:
   - `https://<worker-domain>/webhooks/paddle`
2. Copy endpoint secret from Paddle.
3. Store in worker secret `PADDLE_WEBHOOK_SECRET`.
4. Subscribe to at least:
   - `transaction.completed`
   - `transaction.paid`
   - `transaction.canceled` (or equivalent cancellation/refund events)

## 3) Internal API Access

1. Set `INTERNAL_API_KEY` secret.
2. Restrict usage of internal endpoints to trusted automation/support tooling.
3. Use TLS only.

## 4) Operational Commands

Issue/reissue manually (internal):

```bash
curl -X POST https://<worker-domain>/api/v1/licenses/issue \
  -H "content-type: application/json" \
  -H "x-internal-api-key: <INTERNAL_API_KEY>" \
  -d '{
    "orderId": "txn_123",
    "customerEmail": "customer@example.com",
    "majorVersionMax": 2
  }'
```

Claim token for support flow:

```bash
curl -X POST https://<worker-domain>/api/v1/licenses/claim \
  -H "content-type: application/json" \
  -d '{"orderId":"txn_123","email":"customer@example.com"}'
```

Revoke after refund/chargeback:

```bash
curl -X POST https://<worker-domain>/api/v1/licenses/revoke \
  -H "content-type: application/json" \
  -H "x-internal-api-key: <INTERNAL_API_KEY>" \
  -d '{"orderId":"txn_123","reason":"chargeback"}'
```

## 5) Desktop Integration Contract

Token format:
- `PTL1.<payload_b64url>.<signature_b64url>`

Required claims:
- `kid`
- `tier`
- `license_id`
- `major_version_max`
- `issued_at`

Optional claims:
- `order_id`
- `not_before`
- `expires_at`
- `customer_ref_hash`
- `features` (allowlist)

Desktop app validates signature offline using public keys from `src/license_public_keys.json`.

## 6) Incident Handling

If private key compromise is suspected:

1. Generate a new key pair with a new `kid`.
2. Deploy worker with new signing key secrets.
3. Commit and release desktop update with updated public key list.
4. Reissue active licenses under the new `kid`.
5. Revoke compromised-key licenses where possible.
