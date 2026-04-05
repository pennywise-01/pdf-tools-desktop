import datetime

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from src.utils.license_manager import (
    LicenseManager,
    build_test_token,
    is_pro_feature_name,
)


def _public_key_b64url(private_key: Ed25519PrivateKey) -> str:
    public_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )

    import base64

    return base64.urlsafe_b64encode(public_bytes).decode("ascii").rstrip("=")


def _base_claims(kid: str, major_version_max: int = 2):
    now = datetime.datetime.now(datetime.timezone.utc)
    return {
        "kid": kid,
        "tier": "pro",
        "license_id": "lic-test-001",
        "major_version_max": major_version_max,
        "issued_at": now.isoformat(),
        "not_before": (now - datetime.timedelta(minutes=1)).isoformat(),
        "order_id": "ord_123",
    }


def test_activate_and_persist_license(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))

    private_key = Ed25519PrivateKey.generate()
    kid = "test-kid-v1"
    claims = _base_claims(kid=kid)
    token = build_test_token(private_key, claims)

    manager = LicenseManager(
        app_major_version=2,
        trusted_public_keys={kid: _public_key_b64url(private_key)},
    )
    result = manager.activate_license_key(token)

    assert result.success is True
    assert manager.has_valid_pro_license() is True
    assert manager.can_access_feature("PDF to Word") is True

    # Ensure encrypted local persistence is usable across instances.
    manager2 = LicenseManager(
        app_major_version=2,
        trusted_public_keys={kid: _public_key_b64url(private_key)},
    )
    assert manager2.has_valid_pro_license() is True


def test_rejects_tampered_token(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))

    private_key = Ed25519PrivateKey.generate()
    kid = "test-kid-v1"
    claims = _base_claims(kid=kid)
    token = build_test_token(private_key, claims)

    prefix, payload, signature = token.split(".")

    import base64
    import json

    payload_bytes = base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4))
    payload_data = json.loads(payload_bytes.decode("utf-8"))
    payload_data["license_id"] = "lic-tampered"
    tampered_payload = base64.urlsafe_b64encode(
        json.dumps(payload_data, separators=(",", ":")).encode("utf-8")
    ).decode("ascii").rstrip("=")

    # Keep the original signature to force signature validation failure.
    tampered_token = f"{prefix}.{tampered_payload}.{signature}"

    manager = LicenseManager(
        app_major_version=2,
        trusted_public_keys={kid: _public_key_b64url(private_key)},
    )
    result = manager.activate_license_key(tampered_token)

    assert result.success is False
    assert "signature" in result.message.lower()
    assert manager.has_valid_pro_license() is False


def test_rejects_license_for_older_major_version(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))

    private_key = Ed25519PrivateKey.generate()
    kid = "test-kid-v1"
    claims = _base_claims(kid=kid, major_version_max=1)
    token = build_test_token(private_key, claims)

    manager = LicenseManager(
        app_major_version=2,
        trusted_public_keys={kid: _public_key_b64url(private_key)},
    )
    result = manager.activate_license_key(token)

    assert result.success is False
    assert "major" in result.message.lower()


def test_feature_policy_matrix():
    assert is_pro_feature_name("PDF to PPTX") is True
    assert is_pro_feature_name("Compress") is True
    assert is_pro_feature_name("Merge") is False
    assert is_pro_feature_name("Extract Text") is False


def test_claim_feature_allowlist_is_enforced(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))

    private_key = Ed25519PrivateKey.generate()
    kid = "test-kid-v1"
    claims = _base_claims(kid=kid)
    claims["features"] = ["PDF to Word", "PDF to Excel"]
    token = build_test_token(private_key, claims)

    manager = LicenseManager(
        app_major_version=2,
        trusted_public_keys={kid: _public_key_b64url(private_key)},
    )
    result = manager.activate_license_key(token)

    assert result.success is True
    assert manager.can_access_feature("PDF to Word") is True
    assert manager.can_access_feature("PDF to Excel") is True
    assert manager.can_access_feature("Compress") is False
