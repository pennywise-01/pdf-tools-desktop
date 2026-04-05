import { Env, IssueLicenseInput, PaddleWebhookEvent, StoredLicense } from "./types";
import {
  getLicenseByLicenseId,
  getLicenseByOrderId,
  hasProcessedWebhookEvent,
  markWebhookFailed,
  markWebhookProcessed,
  recordWebhookEvent,
  revokeLicenseByOrderId,
  setLicenseEmailSent,
  upsertLicense,
} from "./lib/db";
import { verifyPaddleWebhookSignature } from "./lib/crypto";
import {
  extractIssueInputFromTransaction,
  fetchPaddleCustomerEmailById,
  extractOrderIdForRevocation,
  isPaymentCompletedEvent,
  isPaymentRevokedEvent,
  parsePaddleWebhookPayload,
} from "./lib/paddle";
import { deriveCustomerRefHash, issueLicenseRecord } from "./lib/license";
import { sendLicenseEmailIfConfigured } from "./lib/email";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json",
      "Cache-Control": "no-store",
    },
  });
}

function utcNowIso(): string {
  return new Date().toISOString();
}

function parseJsonBody<T>(rawBody: string): T {
  try {
    return JSON.parse(rawBody) as T;
  } catch {
    throw new Error("Body must be valid JSON");
  }
}

function normalizeOrderId(payload: Record<string, unknown>): string | undefined {
  const fromCamel = payload.orderId;
  if (typeof fromCamel === "string" && fromCamel.trim()) {
    return fromCamel.trim();
  }

  const fromSnake = payload.order_id;
  if (typeof fromSnake === "string" && fromSnake.trim()) {
    return fromSnake.trim();
  }

  return undefined;
}

function requireInternalAuth(request: Request, env: Env): boolean {
  const header = request.headers.get("x-internal-api-key");
  return !!header && header === env.INTERNAL_API_KEY;
}

function parseDefaultMajorVersion(env: Env): number {
  const raw = env.LICENSE_DEFAULT_MAJOR_VERSION_MAX ?? "2";
  const parsed = Number.parseInt(raw, 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : 2;
}

function normalizeEmail(email: string | undefined): string | undefined {
  if (!email) {
    return undefined;
  }

  const trimmed = email.trim().toLowerCase();
  return trimmed.length > 0 ? trimmed : undefined;
}

async function resolveCustomerEmail(
  env: Env,
  input: IssueLicenseInput,
  existing?: StoredLicense | null,
): Promise<string | undefined> {
  const direct = normalizeEmail(input.customerEmail) ?? normalizeEmail(existing?.customer_email);
  if (direct) {
    return direct;
  }

  const customerId = input.customerId ?? existing?.customer_id;
  if (!customerId) {
    return undefined;
  }

  const fetched = await fetchPaddleCustomerEmailById({
    customerId,
    apiKey: env.PADDLE_API_KEY,
    apiBaseUrl: env.PADDLE_API_BASE_URL,
  });

  return normalizeEmail(fetched);
}

async function issueOrReuseLicense(
  env: Env,
  input: IssueLicenseInput,
): Promise<{ record: StoredLicense; claims?: unknown; issued: boolean }> {
  const existing = await getLicenseByOrderId(env.LICENSING_DB, input.orderId);
  const resolvedCustomerEmail = await resolveCustomerEmail(env, input, existing);

  if (existing && !existing.revoked_at) {
    let record = existing;

    if (resolvedCustomerEmail && !record.customer_email) {
      record = {
        ...record,
        customer_email: resolvedCustomerEmail,
        customer_ref_hash: await deriveCustomerRefHash(resolvedCustomerEmail),
        updated_at: utcNowIso(),
      };
      await upsertLicense(env.LICENSING_DB, record);
    }

    if (resolvedCustomerEmail && !record.last_email_sent_at) {
      const emailResult = await sendLicenseEmailIfConfigured(env, {
        to: resolvedCustomerEmail,
        orderId: record.order_id,
        licenseToken: record.token,
      });

      if (emailResult.sent) {
        const nowIso = utcNowIso();
        await setLicenseEmailSent(env.LICENSING_DB, {
          orderId: record.order_id,
          nowIso,
        });
      }
    }

    const refreshed = (await getLicenseByOrderId(env.LICENSING_DB, input.orderId)) ?? record;
    return { record: refreshed, issued: false };
  }

  const issuanceInput: IssueLicenseInput = {
    ...input,
    customerEmail: resolvedCustomerEmail,
  };

  const issuance = await issueLicenseRecord({
    input: issuanceInput,
    keyId: env.LICENSE_SIGNING_KID,
    privateKeyB64Url: env.LICENSE_SIGNING_PRIVATE_KEY_B64URL,
    existingLicenseId: existing?.license_id,
    defaultMajorVersionMax: parseDefaultMajorVersion(env),
  });

  if (existing?.created_at) {
    issuance.record.created_at = existing.created_at;
  }

  await upsertLicense(env.LICENSING_DB, issuance.record);

  if (issuance.record.customer_email) {
    const emailResult = await sendLicenseEmailIfConfigured(env, {
      to: issuance.record.customer_email,
      orderId: issuance.record.order_id,
      licenseToken: issuance.record.token,
    });
    if (emailResult.sent) {
      await setLicenseEmailSent(env.LICENSING_DB, {
        orderId: issuance.record.order_id,
        nowIso: utcNowIso(),
      });
    }
  }

  const persisted = (await getLicenseByOrderId(env.LICENSING_DB, input.orderId)) ?? issuance.record;
  return { record: persisted, claims: issuance.claims, issued: true };
}

async function processPaddleEvent(env: Env, event: PaddleWebhookEvent): Promise<void> {
  if (isPaymentCompletedEvent(event.event_type)) {
    const input = extractIssueInputFromTransaction(event);
    await issueOrReuseLicense(env, input);
    return;
  }

  if (isPaymentRevokedEvent(event.event_type)) {
    const orderId = extractOrderIdForRevocation(event);
    if (!orderId) {
      return;
    }

    await revokeLicenseByOrderId(env.LICENSING_DB, {
      orderId,
      reason: `revoked_by_${event.event_type}`,
      nowIso: utcNowIso(),
    });
  }
}

async function handlePaddleWebhook(request: Request, env: Env): Promise<Response> {
  const rawBody = await request.text();
  const signatureHeader = request.headers.get("Paddle-Signature");
  const signatureOk = await verifyPaddleWebhookSignature({
    rawBody,
    signatureHeader,
    endpointSecret: env.PADDLE_WEBHOOK_SECRET,
  });

  if (!signatureOk) {
    return jsonResponse({ error: "invalid_signature" }, 401);
  }

  let event: PaddleWebhookEvent;
  try {
    const payload = parseJsonBody<unknown>(rawBody);
    event = parsePaddleWebhookPayload(payload);
  } catch (error) {
    return jsonResponse(
      {
        error: "invalid_payload",
        message: error instanceof Error ? error.message : "Invalid payload",
      },
      400,
    );
  }

  const eventAlreadySeen = await hasProcessedWebhookEvent(env.LICENSING_DB, event.event_id);
  const nowIso = utcNowIso();

  await recordWebhookEvent(env.LICENSING_DB, {
    eventId: event.event_id,
    eventType: event.event_type,
    payloadJson: rawBody,
    nowIso,
  });

  if (eventAlreadySeen) {
    return jsonResponse({ ok: true, status: "duplicate" }, 200);
  }

  try {
    await processPaddleEvent(env, event);
    await markWebhookProcessed(env.LICENSING_DB, {
      eventId: event.event_id,
      nowIso: utcNowIso(),
    });
    return jsonResponse({ ok: true, status: "processed" }, 200);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Webhook processing failed";
    await markWebhookFailed(env.LICENSING_DB, {
      eventId: event.event_id,
      nowIso: utcNowIso(),
      errorMessage: message,
    });
    return jsonResponse({ ok: false, error: "processing_failed", message }, 500);
  }
}

async function handleIssue(request: Request, env: Env): Promise<Response> {
  if (!requireInternalAuth(request, env)) {
    return jsonResponse({ error: "unauthorized" }, 401);
  }

  let payload: Record<string, unknown>;
  try {
    payload = parseJsonBody<Record<string, unknown>>(await request.text());
  } catch (error) {
    return jsonResponse(
      { error: "invalid_payload", message: error instanceof Error ? error.message : "Invalid payload" },
      400,
    );
  }

  const orderId = normalizeOrderId(payload);
  if (!orderId) {
    return jsonResponse({ error: "orderId is required" }, 400);
  }

  const customerId =
    typeof payload.customerId === "string"
      ? payload.customerId
      : typeof payload.customer_id === "string"
        ? payload.customer_id
        : undefined;

  const customerEmail =
    typeof payload.customerEmail === "string"
      ? payload.customerEmail
      : typeof payload.customer_email === "string"
        ? payload.customer_email
        : undefined;

  const majorVersionRaw =
    typeof payload.majorVersionMax === "number"
      ? payload.majorVersionMax
      : typeof payload.majorVersionMax === "string"
        ? Number.parseInt(payload.majorVersionMax, 10)
        : typeof payload.major_version_max === "number"
          ? payload.major_version_max
          : typeof payload.major_version_max === "string"
            ? Number.parseInt(payload.major_version_max, 10)
            : undefined;

  const notBefore =
    typeof payload.notBefore === "string"
      ? payload.notBefore
      : typeof payload.not_before === "string"
        ? payload.not_before
        : undefined;

  const expiresAt =
    typeof payload.expiresAt === "string"
      ? payload.expiresAt
      : typeof payload.expires_at === "string"
        ? payload.expires_at
        : undefined;

  const features = Array.isArray(payload.features)
    ? payload.features.filter((item): item is string => typeof item === "string")
    : undefined;

  const result = await issueOrReuseLicense(env, {
    orderId,
    customerId,
    customerEmail,
    tier: "pro",
    majorVersionMax: Number.isFinite(majorVersionRaw) ? majorVersionRaw : undefined,
    notBefore,
    expiresAt,
    features,
  });

  return jsonResponse(
    {
      issued: result.issued,
      license: {
        license_id: result.record.license_id,
        order_id: result.record.order_id,
        token: result.record.token,
        tier: result.record.tier,
        major_version_max: result.record.major_version_max,
        features: result.record.features ?? null,
        issued_at: result.record.issued_at,
        expires_at: result.record.expires_at ?? null,
        revoked_at: result.record.revoked_at ?? null,
      },
      claims: result.claims ?? null,
    },
    result.issued ? 201 : 200,
  );
}

async function handleClaim(request: Request, env: Env): Promise<Response> {
  let payload: Record<string, unknown>;
  try {
    payload = parseJsonBody<Record<string, unknown>>(await request.text());
  } catch (error) {
    return jsonResponse(
      { error: "invalid_payload", message: error instanceof Error ? error.message : "Invalid payload" },
      400,
    );
  }

  const orderId = normalizeOrderId(payload);
  if (!orderId) {
    return jsonResponse({ error: "orderId is required" }, 400);
  }

  const license = await getLicenseByOrderId(env.LICENSING_DB, orderId);
  if (!license) {
    return jsonResponse({ error: "license_not_found" }, 404);
  }

  if (license.revoked_at) {
    return jsonResponse(
      {
        error: "license_revoked",
        revoked_at: license.revoked_at,
        reason: license.revoked_reason ?? "revoked",
      },
      410,
    );
  }

  const rawEmail =
    typeof payload.email === "string"
      ? payload.email
      : typeof payload.customer_email === "string"
        ? payload.customer_email
        : undefined;
  const email = rawEmail?.trim().toLowerCase();
  if (email && license.customer_email && email !== license.customer_email.toLowerCase()) {
    return jsonResponse({ error: "email_mismatch" }, 403);
  }

  return jsonResponse({
    license: {
      license_id: license.license_id,
      order_id: license.order_id,
      token: license.token,
      tier: license.tier,
      major_version_max: license.major_version_max,
      features: license.features ?? null,
      issued_at: license.issued_at,
      expires_at: license.expires_at ?? null,
    },
  });
}

async function handleRevoke(request: Request, env: Env): Promise<Response> {
  if (!requireInternalAuth(request, env)) {
    return jsonResponse({ error: "unauthorized" }, 401);
  }

  let payload: Record<string, unknown>;
  try {
    payload = parseJsonBody<Record<string, unknown>>(await request.text());
  } catch (error) {
    return jsonResponse(
      { error: "invalid_payload", message: error instanceof Error ? error.message : "Invalid payload" },
      400,
    );
  }

  const orderId = normalizeOrderId(payload);
  if (!orderId) {
    return jsonResponse({ error: "orderId is required" }, 400);
  }

  const reason =
    typeof payload.reason === "string"
      ? payload.reason.trim()
      : typeof payload.revoked_reason === "string"
        ? payload.revoked_reason.trim()
        : "";

  const changes = await revokeLicenseByOrderId(env.LICENSING_DB, {
    orderId,
    reason: reason || "manual_revocation",
    nowIso: utcNowIso(),
  });

  if (changes === 0) {
    return jsonResponse({ error: "not_found_or_already_revoked" }, 404);
  }

  return jsonResponse({ ok: true, orderId });
}

async function handleGetLicense(request: Request, env: Env, licenseId: string): Promise<Response> {
  if (!requireInternalAuth(request, env)) {
    return jsonResponse({ error: "unauthorized" }, 401);
  }

  const license = await getLicenseByLicenseId(env.LICENSING_DB, licenseId);
  if (!license) {
    return jsonResponse({ error: "license_not_found" }, 404);
  }

  return jsonResponse({ license });
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    if (request.method === "GET" && url.pathname === "/health") {
      return jsonResponse({ ok: true, now: utcNowIso() });
    }

    if (request.method === "POST" && url.pathname === "/webhooks/paddle") {
      return handlePaddleWebhook(request, env);
    }

    if (request.method === "POST" && url.pathname === "/api/v1/licenses/issue") {
      return handleIssue(request, env);
    }

    if (request.method === "POST" && url.pathname === "/api/v1/licenses/claim") {
      return handleClaim(request, env);
    }

    if (request.method === "POST" && url.pathname === "/api/v1/licenses/revoke") {
      return handleRevoke(request, env);
    }

    if (request.method === "GET" && url.pathname.startsWith("/api/v1/licenses/")) {
      const licenseId = url.pathname.replace("/api/v1/licenses/", "").trim();
      if (!licenseId) {
        return jsonResponse({ error: "licenseId is required" }, 400);
      }
      return handleGetLicense(request, env, licenseId);
    }

    return jsonResponse({ error: "not_found" }, 404);
  },
};
