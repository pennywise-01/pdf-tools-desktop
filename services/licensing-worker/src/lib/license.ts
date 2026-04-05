import { IssueLicenseInput, LicenseClaims, StoredLicense } from "../types";
import { sha256Hex, signLicenseToken } from "./crypto";

const TOKEN_PREFIX = "PTL1";

function utcNowIso(): string {
  return new Date().toISOString();
}

function normalizeEmail(email: string | undefined): string | undefined {
  if (!email) {
    return undefined;
  }
  const trimmed = email.trim().toLowerCase();
  return trimmed.length > 0 ? trimmed : undefined;
}

export async function deriveCustomerRefHash(email: string | undefined): Promise<string | undefined> {
  const normalized = normalizeEmail(email);
  if (!normalized) {
    return undefined;
  }
  return sha256Hex(normalized);
}

interface BuildClaimsArgs {
  keyId: string;
  licenseId: string;
  orderId: string;
  majorVersionMax: number;
  issuedAt: string;
  notBefore?: string;
  expiresAt?: string;
  customerRefHash?: string;
  features?: string[];
}

export function buildClaims(args: BuildClaimsArgs): LicenseClaims {
  const claims: LicenseClaims = {
    kid: args.keyId,
    tier: "pro",
    license_id: args.licenseId,
    major_version_max: args.majorVersionMax,
    issued_at: args.issuedAt,
    order_id: args.orderId,
  };

  if (args.notBefore) {
    claims.not_before = args.notBefore;
  }
  if (args.expiresAt) {
    claims.expires_at = args.expiresAt;
  }
  if (args.customerRefHash) {
    claims.customer_ref_hash = args.customerRefHash;
  }
  if (args.features && args.features.length > 0) {
    claims.features = args.features;
  }

  return claims;
}

function sanitizeFeatureList(features: string[] | undefined): string[] | undefined {
  if (!features || features.length === 0) {
    return undefined;
  }

  const normalized = Array.from(
    new Set(
      features
        .map((item) => item.trim())
        .filter(Boolean),
    ),
  );

  return normalized.length > 0 ? normalized : undefined;
}

export async function issueLicenseRecord(args: {
  input: IssueLicenseInput;
  keyId: string;
  privateKeyB64Url: string;
  existingLicenseId?: string;
  defaultMajorVersionMax: number;
}): Promise<{ claims: LicenseClaims; token: string; record: StoredLicense }> {
  const nowIso = utcNowIso();
  const majorVersionMax = args.input.majorVersionMax ?? args.defaultMajorVersionMax;
  const features = sanitizeFeatureList(args.input.features);
  const customerEmail = normalizeEmail(args.input.customerEmail);
  const customerRefHash = await deriveCustomerRefHash(customerEmail);
  const licenseId = args.existingLicenseId ?? `lic_${crypto.randomUUID().replace(/-/g, "")}`;

  const claims = buildClaims({
    keyId: args.keyId,
    licenseId,
    orderId: args.input.orderId,
    majorVersionMax,
    issuedAt: nowIso,
    notBefore: args.input.notBefore,
    expiresAt: args.input.expiresAt,
    customerRefHash,
    features,
  });

  const payloadJson = JSON.stringify(claims);
  const token = await signLicenseToken({
    tokenPrefix: TOKEN_PREFIX,
    payloadJson,
    privateKeyB64Url: args.privateKeyB64Url,
  });

  const record: StoredLicense = {
    license_id: licenseId,
    order_id: args.input.orderId,
    customer_id: args.input.customerId,
    customer_email: customerEmail,
    customer_ref_hash: customerRefHash,
    tier: args.input.tier ?? "pro",
    key_id: args.keyId,
    major_version_max: majorVersionMax,
    features,
    issued_at: nowIso,
    not_before: args.input.notBefore,
    expires_at: args.input.expiresAt,
    token,
    created_at: nowIso,
    updated_at: nowIso,
  };

  return { claims, token, record };
}
