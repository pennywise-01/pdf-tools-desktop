# PDF Tools Desktop

A desktop application for various PDF manipulation tools.

## MVP 7 Licensing (Implemented)

The app now supports offline Pro license activation with no runtime outbound network requirement.

### Desktop behavior

- Pro features are marked in the UI and blocked when no valid license is active.
- Activation is manual: users paste a signed license key.
- Validation is local-only using Ed25519 public keys in `src/license_public_keys.json`.
- License payload supports entitlement windows (`not_before`, `expires_at`) and optional feature allowlists.

### Issuance service

A production service scaffold is included at `services/licensing-worker`:

- Paddle webhook verification (`Paddle-Signature` HMAC validation)
- Idempotent event storage and processing
- Signed PTL1 token issuance
- Claim/revoke/internal support endpoints
- Cloudflare D1 persistence

Service setup and API docs:

- `services/licensing-worker/README.md`
- `services/licensing-worker/openapi.yaml`
- `docs/licensing/MVP7_LICENSE_RUNBOOK.md`
- `docs/licensing/MVP7_IMPLEMENTATION_AND_GO_LIVE.md`

### Key tooling

Scripts for key generation and local token issuance:

- `scripts/licensing/generate_license_keys.py`
- `scripts/licensing/issue_license_token.py`

## Security Features

### MVP 8: Anti-Tampering (Implemented)

The application includes comprehensive anti-tampering measures to protect against reverse engineering and unauthorized modifications:

#### 1. Code Obfuscation (PyArmor)
- Advanced bytecode obfuscation with JIT protection
- String literal encryption
- Variable/function name obfuscation

#### 2. Integrity Checks
- SHA-256 checksums verify core files on startup
- Detects modifications to executable or source files
- Automatic termination if tampering is detected

#### 3. Anti-Debugging
- Detects debuggers (x64dbg, IDA Pro, OllyDbg, etc.)
- Detects process monitors and analysis tools
- Hardware breakpoint detection
- Timing-based analysis detection

#### 4. VM Detection
- Identifies virtual machine environments (VirtualBox, VMware, Hyper-V)
- Informational logging for support purposes

### Building with Obfuscation

```bash
# Install dependencies
pip install pyarmor pyinstaller

# Build obfuscated executable
python scripts/build_obfuscated.py
```

### Development Mode

To run in development mode (bypassing anti-tampering checks):

```bash
# Windows PowerShell
$env:PDF_TOOLS_DEV_MODE="1"
python src/main.py

# Windows CMD
set PDF_TOOLS_DEV_MODE=1
python src/main.py

# macOS/Linux
export PDF_TOOLS_DEV_MODE=1
python src/main.py
```

To disable Pro feature blocking during development/testing:

```bash
# Windows PowerShell
$env:PDF_TOOLS_DISABLE_PRO_BLOCK="1"
python src/main.py

# Windows CMD
set PDF_TOOLS_DISABLE_PRO_BLOCK=1
python src/main.py

# macOS/Linux
export PDF_TOOLS_DISABLE_PRO_BLOCK=1
python src/main.py
```

You can combine both toggles when needed.

**⚠️ Never distribute executables built with dev mode enabled!**

For more details, see [docs/ANTI_TAMPERING.md](docs/ANTI_TAMPERING.md).
