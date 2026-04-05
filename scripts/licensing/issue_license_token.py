#!/usr/bin/env python3
"""
Issue a local/offline PTL1 license token for testing and support workflows.
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

TOKEN_PREFIX = "PTL1"
WORKSPACE_ROOT = Path.cwd().resolve()
DEFAULT_PRIVATE_KEY_FILE = WORKSPACE_ROOT / ".secrets/license_private_key.json"
DEFAULT_OUTPUT_FILE = WORKSPACE_ROOT / ".secrets/issued_license_token.json"


def b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def b64url_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def load_private_key(raw_key_b64url: str) -> Ed25519PrivateKey:
    raw_bytes = b64url_decode(raw_key_b64url)
    return Ed25519PrivateKey.from_private_bytes(raw_bytes)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Issue a PTL1 license token")
    parser.add_argument("--kid", required=True, help="Signing key id")
    parser.add_argument("--private-key-b64url", help="Raw Ed25519 private key in base64url")
    parser.add_argument(
        "--use-default-private-key-file",
        action="store_true",
        help="Load private key from .secrets/license_private_key.json",
    )
    parser.add_argument("--license-id", required=True)
    parser.add_argument("--major-version-max", type=int, default=2)
    parser.add_argument("--tier", default="pro")
    parser.add_argument("--order-id", default="")
    parser.add_argument("--customer-ref-hash", default="")
    parser.add_argument("--not-before", default="")
    parser.add_argument("--expires-at", default="")
    parser.add_argument(
        "--features",
        nargs="*",
        default=[],
        help="Optional explicit entitlement allowlist of pro features",
    )
    parser.add_argument(
        "--write-default-output",
        action="store_true",
        help="Write token payload to .secrets/issued_license_token.json",
    )
    return parser.parse_args()


def resolve_private_key_b64url(args: argparse.Namespace) -> str:
    if args.private_key_b64url:
        return args.private_key_b64url.strip()

    if args.use_default_private_key_file:
        payload = json.loads(DEFAULT_PRIVATE_KEY_FILE.read_text(encoding="utf-8"))
        key = str(payload.get("private_key_b64url", "")).strip()
        if key:
            return key

    raise SystemExit("Provide --private-key-b64url or --use-default-private-key-file")


def build_claims(args: argparse.Namespace) -> dict:
    claims = {
        "kid": args.kid,
        "tier": args.tier,
        "license_id": args.license_id,
        "major_version_max": args.major_version_max,
        "issued_at": utc_now_iso(),
    }

    if args.order_id:
        claims["order_id"] = args.order_id
    if args.customer_ref_hash:
        claims["customer_ref_hash"] = args.customer_ref_hash
    if args.not_before:
        claims["not_before"] = args.not_before
    if args.expires_at:
        claims["expires_at"] = args.expires_at
    if args.features:
        claims["features"] = args.features

    return claims


def build_token(private_key: Ed25519PrivateKey, claims: dict) -> str:
    payload_json = json.dumps(claims, separators=(",", ":")).encode("utf-8")
    payload_b64 = b64url_encode(payload_json)
    signed_data = f"{TOKEN_PREFIX}.{payload_b64}".encode("ascii")
    signature = private_key.sign(signed_data)
    signature_b64 = b64url_encode(signature)
    return f"{TOKEN_PREFIX}.{payload_b64}.{signature_b64}"


def main() -> int:
    args = parse_args()
    private_b64url = resolve_private_key_b64url(args)
    private_key = load_private_key(private_b64url)

    # Validate key object by deriving the public key once.
    _ = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )

    claims = build_claims(args)
    token = build_token(private_key, claims)

    output = {
        "token": token,
        "claims": claims,
    }

    if args.write_default_output:
        out = DEFAULT_OUTPUT_FILE
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote token: {out}")
    else:
        print(token)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
