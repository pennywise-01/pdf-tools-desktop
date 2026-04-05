import * as ed from "@noble/ed25519";

const encoder = new TextEncoder();

export function b64urlEncode(value: Uint8Array): string {
  let binary = "";
  for (const byte of value) {
    binary += String.fromCharCode(byte);
  }
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

export function b64urlDecode(value: string): Uint8Array {
  const normalized = value.replace(/-/g, "+").replace(/_/g, "/");
  const padded = normalized + "=".repeat((4 - (normalized.length % 4 || 4)) % 4);
  const binary = atob(padded);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

function bytesToHex(value: Uint8Array): string {
  return Array.from(value, (byte) => byte.toString(16).padStart(2, "0")).join("");
}

function timingSafeEqualHex(left: string, right: string): boolean {
  if (left.length !== right.length) {
    return false;
  }

  let mismatch = 0;
  for (let i = 0; i < left.length; i += 1) {
    mismatch |= left.charCodeAt(i) ^ right.charCodeAt(i);
  }
  return mismatch === 0;
}

export async function sha256Hex(value: string): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", encoder.encode(value));
  return bytesToHex(new Uint8Array(digest));
}

interface ParsedPaddleSignature {
  timestamp: number;
  signatures: string[];
}

function parsePaddleSignature(header: string): ParsedPaddleSignature {
  const entries = header
    .split(";")
    .map((part) => part.trim())
    .filter(Boolean)
    .map((part) => {
      const [key, value] = part.split("=");
      return { key, value };
    });

  const timestampValue = entries.find((entry) => entry.key === "ts")?.value;
  const signatures = entries
    .filter((entry) => entry.key === "h1" && !!entry.value)
    .map((entry) => entry.value);

  if (!timestampValue || signatures.length === 0) {
    throw new Error("Malformed Paddle-Signature header");
  }

  const timestamp = Number.parseInt(timestampValue, 10);
  if (!Number.isFinite(timestamp)) {
    throw new Error("Invalid Paddle-Signature timestamp");
  }

  return { timestamp, signatures };
}

async function hmacSha256Hex(secret: string, payload: string): Promise<string> {
  const key = await crypto.subtle.importKey(
    "raw",
    encoder.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );

  const signature = await crypto.subtle.sign("HMAC", key, encoder.encode(payload));
  return bytesToHex(new Uint8Array(signature));
}

export async function verifyPaddleWebhookSignature(args: {
  rawBody: string;
  signatureHeader: string | null;
  endpointSecret: string;
  toleranceSeconds?: number;
}): Promise<boolean> {
  const { rawBody, signatureHeader, endpointSecret, toleranceSeconds = 300 } = args;

  if (!signatureHeader) {
    return false;
  }

  if (!endpointSecret || endpointSecret.trim().length === 0) {
    return false;
  }

  let parsed: ParsedPaddleSignature;
  try {
    parsed = parsePaddleSignature(signatureHeader);
  } catch {
    return false;
  }

  const nowUnix = Math.floor(Date.now() / 1000);
  if (Math.abs(nowUnix - parsed.timestamp) > toleranceSeconds) {
    return false;
  }

  const payload = `${parsed.timestamp}:${rawBody}`;
  let expected: string;
  try {
    expected = await hmacSha256Hex(endpointSecret, payload);
  } catch {
    return false;
  }

  return parsed.signatures.some((candidate) => timingSafeEqualHex(candidate, expected));
}

export async function signLicenseToken(args: {
  tokenPrefix: string;
  payloadJson: string;
  privateKeyB64Url: string;
}): Promise<string> {
  const payloadB64 = b64urlEncode(encoder.encode(args.payloadJson));
  const toSign = encoder.encode(`${args.tokenPrefix}.${payloadB64}`);
  const privateKey = b64urlDecode(args.privateKeyB64Url);
  const signature = await ed.signAsync(toSign, privateKey);
  const signatureB64 = b64urlEncode(signature);
  return `${args.tokenPrefix}.${payloadB64}.${signatureB64}`;
}
