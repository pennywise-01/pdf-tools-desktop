import { IssueLicenseInput, PaddleWebhookEvent } from "../types";

function isObject(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === "object" && !Array.isArray(value);
}

function readString(value: unknown): string | undefined {
  if (typeof value !== "string") {
    return undefined;
  }
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : undefined;
}

export function parsePaddleWebhookPayload(payload: unknown): PaddleWebhookEvent {
  if (!isObject(payload)) {
    throw new Error("Webhook payload must be an object");
  }

  const eventId = readString(payload.event_id) ?? readString(payload.notification_id);
  const eventType = readString(payload.event_type);
  const occurredAt = readString(payload.occurred_at);
  const data = isObject(payload.data) ? payload.data : {};

  if (!eventId) {
    throw new Error("Webhook payload missing event_id");
  }
  if (!eventType) {
    throw new Error("Webhook payload missing event_type");
  }

  return {
    event_id: eventId,
    event_type: eventType,
    occurred_at: occurredAt,
    data,
  };
}

export function extractIssueInputFromTransaction(event: PaddleWebhookEvent): IssueLicenseInput {
  const data = event.data;

  const orderId =
    readString(data.id) ??
    readString(data.transaction_id) ??
    readString(data.order_id);

  if (!orderId) {
    throw new Error("Unable to determine order id from transaction event");
  }

  let customerEmail: string | undefined;
  let customerId: string | undefined;

  const customerValue = data.customer;
  if (isObject(customerValue)) {
    customerEmail = readString(customerValue.email);
    customerId = readString(customerValue.id);
  }

  customerEmail = customerEmail ?? readString(data.customer_email);
  customerId = customerId ?? readString(data.customer_id);

  const billingDetails = isObject(data.billing_details) ? data.billing_details : {};
  customerEmail = customerEmail ?? readString(billingDetails.email);

  const customData = isObject(data.custom_data) ? data.custom_data : {};

  const majorVersionRaw = customData.major_version_max;
  const majorVersionMax =
    typeof majorVersionRaw === "number"
      ? majorVersionRaw
      : typeof majorVersionRaw === "string"
        ? Number.parseInt(majorVersionRaw, 10)
        : undefined;

  const notBefore = readString(customData.not_before);
  const expiresAt = readString(customData.expires_at);

  let features: string[] | undefined;
  const featureRaw = customData.features;
  if (Array.isArray(featureRaw)) {
    const normalized = featureRaw
      .filter((item): item is string => typeof item === "string")
      .map((item) => item.trim())
      .filter(Boolean);
    if (normalized.length > 0) {
      features = normalized;
    }
  }

  return {
    orderId,
    customerId,
    customerEmail,
    majorVersionMax: Number.isFinite(majorVersionMax) ? majorVersionMax : undefined,
    notBefore,
    expiresAt,
    features,
    tier: "pro",
  };
}

function normalizeApiBaseUrl(url: string): string {
  return url.trim().replace(/\/+$/, "");
}

function candidateApiBaseUrls(apiBaseUrl?: string): string[] {
  const explicit = readString(apiBaseUrl);
  if (explicit) {
    return [normalizeApiBaseUrl(explicit)];
  }

  return ["https://api.paddle.com", "https://sandbox-api.paddle.com"];
}

export async function fetchPaddleCustomerEmailById(args: {
  customerId: string;
  apiKey?: string;
  apiBaseUrl?: string;
}): Promise<string | undefined> {
  const customerId = readString(args.customerId);
  const apiKey = readString(args.apiKey);
  if (!customerId || !apiKey) {
    return undefined;
  }

  for (const baseUrl of candidateApiBaseUrls(args.apiBaseUrl)) {
    const response = await fetch(`${baseUrl}/customers/${encodeURIComponent(customerId)}`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        Accept: "application/json",
      },
    });

    if (!response.ok) {
      continue;
    }

    let payload: unknown;
    try {
      payload = await response.json();
    } catch {
      continue;
    }

    if (!isObject(payload)) {
      continue;
    }

    const data = isObject(payload.data) ? payload.data : {};
    const email = readString(data.email);
    if (email) {
      return email;
    }
  }

  return undefined;
}

export function extractOrderIdForRevocation(event: PaddleWebhookEvent): string | undefined {
  const data = event.data;
  return readString(data.id) ?? readString(data.transaction_id) ?? readString(data.order_id);
}

export function isPaymentCompletedEvent(eventType: string): boolean {
  return eventType === "transaction.completed" || eventType === "transaction.paid";
}

export function isPaymentRevokedEvent(eventType: string): boolean {
  return (
    eventType === "transaction.canceled" ||
    eventType === "transaction.cancelled" ||
    eventType === "adjustment.updated"
  );
}
