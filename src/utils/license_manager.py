import base64
import datetime
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

TOKEN_PREFIX = "PTL1"
APP_MAJOR_VERSION = 2

# Complex tasks in MVP 3-6 + PDF to PPTX (agreed MVP 7 scope)
PRO_FEATURE_NAMES = frozenset(
    {
        "HTML to PDF",
        "PDF to Images",
        "Compress",
        "Redact",
        "OCR (Text)",
        "Office to PDF",
        "PDF to Excel",
        "PDF to Word",
        "PDF to PPTX",
    }
)


def is_pro_feature_name(feature_name: str) -> bool:
    return feature_name in PRO_FEATURE_NAMES


def _utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def _parse_datetime(value: str) -> datetime.datetime:
    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    parsed = datetime.datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=datetime.timezone.utc)
    return parsed.astimezone(datetime.timezone.utc)


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _load_public_keys_from_env() -> Dict[str, str]:
    """
    Optional override for development/testing.
    Format:
        PDF_TOOLS_LICENSE_PUBLIC_KEYS='{"kid1":"base64url_key_bytes"}'
    """
    raw = os.environ.get("PDF_TOOLS_LICENSE_PUBLIC_KEYS", "").strip()
    if not raw:
        return {}

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}

    if not isinstance(parsed, dict):
        return {}

    clean: Dict[str, str] = {}
    for key_id, key_material in parsed.items():
        if isinstance(key_id, str) and isinstance(key_material, str):
            clean[key_id] = key_material
    return clean


def _load_public_keys_from_file() -> Dict[str, str]:
    """
    Load trusted public keys from src/license_public_keys.json.
    File format:
        {
          "kid1": "base64url_key_bytes",
          "kid2": "base64url_key_bytes"
        }
    """
    candidate = Path(__file__).resolve().parent.parent / "license_public_keys.json"
    if not candidate.exists():
        return {}

    try:
        parsed = json.loads(candidate.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    if not isinstance(parsed, dict):
        return {}

    clean: Dict[str, str] = {}
    for key_id, key_material in parsed.items():
        if isinstance(key_id, str) and isinstance(key_material, str):
            clean[key_id] = key_material
    return clean


def load_trusted_public_keys() -> Dict[str, str]:
    """
    Merge key sources with env taking precedence for emergency overrides.
    """
    return {
        **_load_public_keys_from_file(),
        **_load_public_keys_from_env(),
    }


@dataclass
class LicenseStatus:
    is_active: bool
    tier: str
    reason: str = ""
    claims: Optional[dict] = None


@dataclass
class ActivationResult:
    success: bool
    message: str
    status: LicenseStatus


class LicenseManager:
    """
    Offline license validation and local secure persistence.

    License key format:
        PTL1.<base64url(payload_json)>. <base64url(signature_bytes)>

    Signature algorithm:
        Ed25519 over the bytes of "PTL1.<payload_b64>"

    Required payload fields:
        kid, tier, license_id, major_version_max, issued_at

    Optional payload fields:
        not_before, expires_at, customer_ref_hash, order_id
    """

    STORE_FILE = "license.dat"
    STORE_KEY_FILE = "license_store.key"

    def __init__(
        self,
        app_major_version: int = APP_MAJOR_VERSION,
        trusted_public_keys: Optional[Dict[str, str]] = None,
    ):
        self.app_major_version = app_major_version
        self.trusted_public_keys = trusted_public_keys or load_trusted_public_keys()
        self.app_data_dir = Path(os.getenv("APPDATA") or Path.home()) / "PDFToolsDesktop"
        self.app_data_dir.mkdir(parents=True, exist_ok=True)

        self.store_path = self.app_data_dir / self.STORE_FILE
        self.store_key_path = self.app_data_dir / self.STORE_KEY_FILE

        self._cipher = Fernet(self._load_or_generate_store_key())
        self._cached_status: Optional[LicenseStatus] = None

    def _load_or_generate_store_key(self) -> bytes:
        if self.store_key_path.exists():
            return self.store_key_path.read_bytes()

        key = Fernet.generate_key()
        self.store_key_path.write_bytes(key)
        return key

    def _log_event(self, action: str, details: dict) -> None:
        try:
            from utils.audit_log import audit_logger
        except Exception:
            return

        try:
            audit_logger.log_event(action, details)
        except Exception:
            pass

    def _decrypt_stored_record(self) -> Optional[dict]:
        if not self.store_path.exists():
            return None

        try:
            encrypted = self.store_path.read_bytes()
            decrypted = self._cipher.decrypt(encrypted)
            record = json.loads(decrypted.decode("utf-8"))
            if not isinstance(record, dict):
                return None
            return record
        except (InvalidToken, OSError, json.JSONDecodeError):
            self._log_event(
                "license_store_corrupted",
                {"path": str(self.store_path)},
            )
            return None

    def _save_record(self, record: dict) -> None:
        encoded = json.dumps(record, separators=(",", ":")).encode("utf-8")
        encrypted = self._cipher.encrypt(encoded)
        self.store_path.write_bytes(encrypted)

    def _validate_claims(self, claims: dict) -> LicenseStatus:
        required_claims = ["kid", "tier", "license_id", "major_version_max", "issued_at"]
        for claim_name in required_claims:
            if claim_name not in claims:
                return LicenseStatus(False, "free", f"Missing claim: {claim_name}")

        if claims.get("tier") != "pro":
            return LicenseStatus(False, "free", "License tier is not pro")

        try:
            major_max = int(claims.get("major_version_max"))
        except (TypeError, ValueError):
            return LicenseStatus(False, "free", "Invalid major_version_max")

        if major_max < self.app_major_version:
            return LicenseStatus(
                False,
                "free",
                f"License supports app major <= {major_max}",
            )

        try:
            issued_at = _parse_datetime(str(claims.get("issued_at")))
        except Exception:
            return LicenseStatus(False, "free", "Invalid issued_at value")

        now = _utc_now()
        if issued_at > now + datetime.timedelta(minutes=10):
            return LicenseStatus(False, "free", "License issued_at is in the future")

        not_before_raw = claims.get("not_before")
        if isinstance(not_before_raw, str):
            try:
                not_before = _parse_datetime(not_before_raw)
            except Exception:
                return LicenseStatus(False, "free", "Invalid not_before value")
            if now < not_before:
                return LicenseStatus(False, "free", "License not active yet")

        expires_at_raw = claims.get("expires_at")
        if isinstance(expires_at_raw, str):
            try:
                expires_at = _parse_datetime(expires_at_raw)
            except Exception:
                return LicenseStatus(False, "free", "Invalid expires_at value")
            if now > expires_at:
                return LicenseStatus(False, "free", "License has expired")

        return LicenseStatus(True, "pro", claims=claims)

    def _validate_signature(self, token: str) -> LicenseStatus:
        if not self.trusted_public_keys:
            return LicenseStatus(
                False,
                "free",
                "No trusted public keys configured",
            )

        parts = token.strip().split(".")
        if len(parts) != 3:
            return LicenseStatus(False, "free", "Invalid license format")

        prefix, payload_b64, signature_b64 = parts
        if prefix != TOKEN_PREFIX:
            return LicenseStatus(False, "free", "Unsupported token prefix")

        try:
            payload_raw = _b64url_decode(payload_b64)
            signature = _b64url_decode(signature_b64)
        except Exception:
            return LicenseStatus(False, "free", "Invalid base64 encoding")

        try:
            claims = json.loads(payload_raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return LicenseStatus(False, "free", "Invalid payload JSON")

        if not isinstance(claims, dict):
            return LicenseStatus(False, "free", "Payload must be a JSON object")

        key_id = claims.get("kid")
        if not isinstance(key_id, str) or not key_id:
            return LicenseStatus(False, "free", "Missing key id")

        key_material = self.trusted_public_keys.get(key_id)
        if not key_material:
            return LicenseStatus(False, "free", f"Unknown key id: {key_id}")

        try:
            public_key = Ed25519PublicKey.from_public_bytes(_b64url_decode(key_material))
            signed_data = f"{TOKEN_PREFIX}.{payload_b64}".encode("ascii")
            public_key.verify(signature, signed_data)
        except Exception:
            return LicenseStatus(False, "free", "Invalid signature")

        claims_status = self._validate_claims(claims)
        if not claims_status.is_active:
            return claims_status

        return LicenseStatus(True, "pro", claims=claims)

    def activate_license_key(self, token: str) -> ActivationResult:
        status = self._validate_signature(token)
        if not status.is_active:
            self._log_event(
                "license_activation_failed",
                {"reason": status.reason},
            )
            return ActivationResult(False, status.reason, status)

        record = {
            "token": token.strip(),
            "claims": status.claims,
            "activated_at": _utc_now().isoformat(),
        }

        try:
            self._save_record(record)
        except OSError:
            failed_status = LicenseStatus(False, "free", "Could not save license locally")
            return ActivationResult(False, failed_status.reason, failed_status)

        self._cached_status = status
        self._log_event(
            "license_activated",
            {
                "tier": status.tier,
                "license_id": status.claims.get("license_id") if status.claims else None,
                "major_version_max": status.claims.get("major_version_max") if status.claims else None,
            },
        )
        return ActivationResult(True, "License activated successfully", status)

    def clear_local_license(self) -> None:
        try:
            if self.store_path.exists():
                self.store_path.unlink()
        except OSError:
            pass
        self._cached_status = LicenseStatus(False, "free", "No license activated")
        self._log_event("license_cleared", {})

    def refresh_status(self) -> LicenseStatus:
        record = self._decrypt_stored_record()
        if not record:
            self._cached_status = LicenseStatus(False, "free", "No license activated")
            return self._cached_status

        token = record.get("token")
        if not isinstance(token, str) or not token.strip():
            self._cached_status = LicenseStatus(False, "free", "Stored license is malformed")
            return self._cached_status

        status = self._validate_signature(token)
        self._cached_status = status

        if not status.is_active:
            self._log_event("stored_license_invalid", {"reason": status.reason})

        return status

    def get_status(self) -> LicenseStatus:
        if self._cached_status is None:
            return self.refresh_status()
        return self._cached_status

    def has_valid_pro_license(self) -> bool:
        status = self.get_status()
        if status.is_active:
            return True

        # Attempt refresh in case license changed externally since startup.
        status = self.refresh_status()
        return status.is_active

    def can_access_feature(self, feature_name: str) -> bool:
        if not is_pro_feature_name(feature_name):
            return True

        status = self.get_status()
        if not status.is_active:
            status = self.refresh_status()
            if not status.is_active:
                return False

        claims = status.claims or {}
        entitled_features = claims.get("features")
        if isinstance(entitled_features, list):
            entitled_set = {str(item) for item in entitled_features}
            return feature_name in entitled_set

        return True

    def record_pro_gate_denied(self, feature_name: str) -> None:
        status = self.get_status()
        self._log_event(
            "pro_feature_denied",
            {
                "feature": feature_name,
                "reason": status.reason,
                "tier": status.tier,
            },
        )

    def get_license_summary(self) -> dict:
        status = self.get_status()
        claims = status.claims or {}
        return {
            "is_active": status.is_active,
            "tier": status.tier,
            "reason": status.reason,
            "license_id": claims.get("license_id"),
            "major_version_max": claims.get("major_version_max"),
            "issued_at": claims.get("issued_at"),
            "not_before": claims.get("not_before"),
            "expires_at": claims.get("expires_at"),
        }


def build_test_token(private_key, claims: dict) -> str:
    """
    Helper for tests and local tooling only.
    Not used by production runtime.
    """
    payload_json = json.dumps(claims, separators=(",", ":")).encode("utf-8")
    payload_b64 = _b64url_encode(payload_json)
    signed_data = f"{TOKEN_PREFIX}.{payload_b64}".encode("ascii")
    signature = private_key.sign(signed_data)
    signature_b64 = _b64url_encode(signature)
    return f"{TOKEN_PREFIX}.{payload_b64}.{signature_b64}"
