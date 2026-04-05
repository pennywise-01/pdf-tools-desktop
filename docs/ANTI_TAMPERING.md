# Anti-Tampering Guide (MVP 8)

This document describes the anti-tampering measures implemented in PDF Tools Desktop and how to use them.

## Overview

MVP 8 implements three layers of protection:

1. **Code Obfuscation** - PyArmor protects Python source code
2. **Integrity Checks** - SHA-256 checksums verify file integrity
3. **Anti-Debugging** - Detects and blocks debugging/analysis tools

## Security Layers

### 1. Code Obfuscation (PyArmor)

PyArmor obfuscates Python bytecode to make reverse engineering significantly more difficult.

**Features:**
- Advanced obfuscation mode with JIT protection
- String literal encryption (`mix-str`)
- Variable/function name obfuscation (`enable-rft`)
- Cross-platform protection

### 2. Integrity Checks

The application verifies its own files on startup using SHA-256 checksums.

**How it works:**
- Checksums are generated during the build process
- At runtime, files are hashed and compared
- Any modification triggers immediate termination

**Protected files include:**
- Main executable
- Python source files (in development mode)
- Critical security modules

### 3. Anti-Debugging Measures

The application detects common debugging and analysis tools.

**Detected threats:**
- Debuggers (x64dbg, IDA Pro, OllyDbg, GDB, etc.)
- Process monitors (Process Hacker, ProcMon, etc.)
- Analysis tools (Cheat Engine, Wireshark, etc.)
- Hardware breakpoints
- Timing-based detection

**VM Detection:**
- VirtualBox, VMware, Hyper-V indicators are logged
- Does not block execution (informational only)
- Useful for analytics and support

## Build Instructions

### Prerequisites

```bash
pip install pyarmor pyinstaller
```

### Option 1: Using the Build Script (Recommended)

```bash
python scripts/build_obfuscated.py
```

This script performs all steps:
1. Generates integrity checksums
2. Obfuscates code with PyArmor
3. Packages with PyInstaller
4. Signs executable (if certificate available)
5. Verifies the final build

### Option 2: Manual Build Steps

#### Step 1: Generate Integrity Checksums

```bash
cd src
python -c "from utils.anti_tampering import IntegrityChecker; c = IntegrityChecker(); c.save_checksums()"
```

#### Step 2: Obfuscate with PyArmor

```bash
pyarmor gen --output dist/obfuscated --recursive --restrict --mix-str --enable-rft --enable-jit --advance-mode 2 src
```

#### Step 3: Copy Assets

```bash
cp src/.integrity_checksums.json dist/obfuscated/
cp src/style.qss dist/obfuscated/
cp -r icon dist/obfuscated/
```

#### Step 4: Package with PyInstaller

```bash
pyinstaller --name PDFToolsDesktop --onefile --windowed --icon icon/pdf-app-icon.ico dist/obfuscated/main.py
```

## Development Mode

During development, you can disable anti-tampering checks:

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

**⚠️ Never distribute executables built with dev mode enabled!**

## Testing Anti-Tampering

### Test Integrity Checks

```bash
python src/utils/anti_tampering.py
```

Expected output:
```
Testing Anti-Tampering Module...
==================================================
[1] Integrity Checker Test
Base path: C:\...\src
Checksum file: C:\...\src\.integrity_checksums.json
...
Integrity check: PASSED
```

### Test Anti-Debug

Run the tests with a debugger attached:
- The application should exit immediately
- Check stderr for: "SECURITY ALERT: Debugging/analysis tools detected"

## Configuration

### PyArmor Configuration

Edit `pyarmor_config.json` to customize obfuscation:

```json
{
  "obfuscation": {
    "mode": "advanced",
    "restrict": 1,
    "mix_str": 1,
    "mix_name": 2,
    "advanced_mode": 2
  }
}
```

Options:
- `mode`: `simple`, `advanced`, or `super`
- `mix_str`: Encrypt string literals (0 or 1)
- `mix_name`: Variable renaming level (0-2)
- `advanced_mode`: Protection level (1-2)

### Integrity Check Configuration

Modify `src/utils/anti_tampering.py`:

```python
class IntegrityChecker:
    def get_core_files(self) -> List[str]:
        # Add files to protect
        core_files.append('path/to/file.py')
```

## Troubleshooting

### "Integrity checksums file not found"

**Cause:** Checksums weren't generated before running.

**Fix:**
```bash
cd src
python -c "from utils.anti_tampering import IntegrityChecker; c = IntegrityChecker(); c.save_checksums()"
```

### "Debugging/analysis tools detected"

**Cause:** A debugger or analysis tool is running.

**Fix:** Close all debugging tools before running the application.

### PyArmor errors during build

**Common solutions:**
1. Update PyArmor: `pip install -U pyarmor`
2. Clear cache: `pyarmor clear`
3. Check Python version compatibility

## Security Considerations

1. **Checksum Storage**: Checksums are stored in `.integrity_checksums.json`. In production, consider embedding this in the binary or encrypting it.

2. **Code Signing**: For production releases, use a valid code signing certificate to prevent OS warnings.

3. **License Integration**: Anti-tampering works best when combined with the licensing system (MVP 7).

4. **No Perfect Security**: These measures deter casual reverse engineering but cannot stop determined attackers. Consider them as part of a defense-in-depth strategy.

## Integration with Licensing

To integrate with MVP 7's license validation:

```python
# In your license module
from utils.anti_tampering import verify_application_integrity

def validate_license(key: str) -> bool:
    # Verify integrity before checking license
    if not verify_application_integrity(exit_on_failure=False):
        return False
    
    # ... license validation logic ...
```

## Updating Checksums

Whenever you modify protected files, regenerate checksums:

```bash
# Delete old checksums
del src\.integrity_checksums.json

# Generate new ones
python src/utils/anti_tampering.py
```

## Platform-Specific Notes

### Windows
- Anti-debug uses Windows API (IsDebuggerPresent, GetThreadContext)
- Code signing uses signtool (Windows SDK)

### macOS
- VM detection uses system_profiler
- Consider notarizing the app for Gatekeeper compliance

### Linux
- VM detection checks /proc/cpuinfo and DMI tables
- May require root for some detection methods

## Performance Impact

Anti-tampering checks add minimal overhead:
- Integrity check: ~50-100ms on startup
- Anti-debug check: ~10-20ms
- Total impact: <200ms startup delay

## References

- [PyArmor Documentation](https://pyarmor.readthedocs.io/)
- [PyInstaller Documentation](https://pyinstaller.readthedocs.io/)
- [Windows Anti-Debug Techniques](https://anti-debug.checkpoint.com/)
