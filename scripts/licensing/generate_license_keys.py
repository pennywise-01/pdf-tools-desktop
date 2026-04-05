#!/usr/bin/env python3
"""
Generate Ed25519 signing keys for offline license tokens.

This script writes:
1) Public key material into src/license_public_keys.json (safe to commit)
2) Private key material into a local file (DO NOT commit)
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


WORKSPACE_ROOT = Path.cwd().resolve()
PUBLIC_KEYS_FILE = WORKSPACE_ROOT / "src/license_public_keys.json"
PRIVATE_OUTPUT_FILE = WORKSPACE_ROOT / ".secrets/license_private_key.json"


def b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Ed25519 license signing keys")
    parser.add_argument(
        "--kid",
        default=f"prod-{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%d')}",
        help="Key identifier for rotation (default: prod-YYYYMMDD)",
    )
    return parser.parse_args()


def load_public_keys(path: Path) -> dict:
    if not path.exists():
        return {}

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}")

    if not isinstance(payload, dict):
        raise SystemExit(f"Expected object in {path}")

    return {str(k): str(v) for k, v in payload.items()}


def main() -> int:
    args = parse_args()

    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    private_raw = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_raw = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )

    private_b64url = b64url_encode(private_raw)
    public_b64url = b64url_encode(public_raw)

    public_file = PUBLIC_KEYS_FILE
    public_file.parent.mkdir(parents=True, exist_ok=True)

    public_keys = load_public_keys(public_file)
    public_keys[args.kid] = public_b64url
    public_file.write_text(json.dumps(public_keys, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    private_file = PRIVATE_OUTPUT_FILE
    private_file.parent.mkdir(parents=True, exist_ok=True)
    private_payload = {
        "kid": args.kid,
        "private_key_b64url": private_b64url,
        "public_key_b64url": public_b64url,
        "created_at": utc_now_iso(),
    }
    private_file.write_text(json.dumps(private_payload, indent=2) + "\n", encoding="utf-8")

    print("Key generation complete.")
    print(f"Public key updated: {public_file}")
    print(f"Private key written: {private_file}")
    print()
    print("Set these secrets in the license service:")
    print(f"LICENSE_SIGNING_KID={args.kid}")
    print(f"LICENSE_SIGNING_PRIVATE_KEY_B64URL={private_b64url}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
