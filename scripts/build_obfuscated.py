#!/usr/bin/env python3
"""
Build script for obfuscating PDF Tools Desktop with PyArmor.
This script handles the complete obfuscation and packaging process.
"""

import os
import sys
import subprocess
import shutil
import json
import hashlib
from pathlib import Path

# Ensure we're running from the project root
PROJECT_ROOT = Path(__file__).parent.parent
os.chdir(PROJECT_ROOT)

SRC_DIR = PROJECT_ROOT / "src"
DIST_DIR = PROJECT_ROOT / "dist"
OBF_DIR = DIST_DIR / "obfuscated"
INTEGRITY_FILE = SRC_DIR / ".integrity_checksums.json"


def run_command(cmd: list, check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def check_pyarmor():
    """Check if pyarmor is installed."""
    try:
        result = run_command(["pyarmor", "--version"], check=False)
        if result.returncode == 0:
            print(f"PyArmor version: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    print("ERROR: PyArmor not found. Install it with: pip install pyarmor")
    return False


def generate_integrity_checksums():
    """Generate checksums for source files before obfuscation."""
    print("\n[1] Generating integrity checksums...")
    
    # Import the anti_tampering module
    sys.path.insert(0, str(SRC_DIR))
    from utils.anti_tampering import IntegrityChecker
    
    checker = IntegrityChecker(str(SRC_DIR))
    checksums = checker.generate_checksums()
    checker.save_checksums(checksums)
    
    print(f"Generated {len(checksums)} checksums to {INTEGRITY_FILE}")
    return checksums


def obfuscate_code():
    """Obfuscate the Python code using PyArmor."""
    print("\n[2] Obfuscating Python code with PyArmor...")
    
    # Clean previous obfuscation
    if OBF_DIR.exists():
        shutil.rmtree(OBF_DIR)
    OBF_DIR.mkdir(parents=True, exist_ok=True)
    
    # Build command for pyarmor
    # Using advanced mode with maximum protection
    cmd = [
        "pyarmor", "gen",
        "--output", str(OBF_DIR),
        "--recursive",
        "--restrict",
        "--mix-str",
        "--enable-rft",  # Rename function/variable names
        "--enable-jit",  # JIT protection
        "--advance-mode", "2",  # Maximum obfuscation
        "--platform", "windows.x86_64",
        "--platform", "darwin.x86_64", 
        "--platform", "linux.x86_64",
        str(SRC_DIR)
    ]
    
    result = run_command(cmd, check=False)
    
    if result.returncode != 0:
        print(f"ERROR: PyArmor failed:\n{result.stderr}")
        return False
    
    print("Obfuscation completed successfully.")
    return True


def copy_assets():
    """Copy non-Python assets to obfuscated directory."""
    print("\n[3] Copying assets...")
    
    # Copy checksums file
    if INTEGRITY_FILE.exists():
        shutil.copy(INTEGRITY_FILE, OBF_DIR / ".integrity_checksums.json")
        print("Copied integrity checksums")
    
    # Copy QSS style file
    style_file = SRC_DIR / "style.qss"
    if style_file.exists():
        shutil.copy(style_file, OBF_DIR / "style.qss")
        print("Copied style.qss")
    
    # Copy icons
    icon_dir = PROJECT_ROOT / "icon"
    if icon_dir.exists():
        dest_icon_dir = OBF_DIR / "icon"
        if dest_icon_dir.exists():
            shutil.rmtree(dest_icon_dir)
        shutil.copytree(icon_dir, dest_icon_dir)
        print(f"Copied icons ({len(list(icon_dir.glob('*')))} files)")
    
    return True


def package_with_pyinstaller():
    """Package obfuscated code with PyInstaller."""
    print("\n[4] Packaging with PyInstaller...")
    
    spec_file = PROJECT_ROOT / "pdf_tools.spec"
    
    if spec_file.exists():
        # Use existing spec file
        cmd = ["pyinstaller", str(spec_file), "--clean"]
    else:
        # Create standalone executable
        cmd = [
            "pyinstaller",
            "--name", "PDFToolsDesktop",
            "--onefile",
            "--windowed",
            "--icon", str(PROJECT_ROOT / "icon" / "pdf-app-icon.ico"),
            "--add-data", f"{OBF_DIR / 'style.qss'};src",
            "--add-data", f"{OBF_DIR / 'icon'};icon",
            "--add-data", f"{OBF_DIR / '.integrity_checksums.json'};src",
            "--clean",
            str(OBF_DIR / "main.py")
        ]
    
    result = run_command(cmd, check=False)
    
    if result.returncode != 0:
        print(f"ERROR: PyInstaller failed:\n{result.stderr}")
        return False
    
    print("Packaging completed successfully.")
    return True


def sign_executable():
    """Sign the executable with a code signing certificate (if available)."""
    print("\n[5] Code signing...")
    
    # Check for signing certificate
    cert_file = PROJECT_ROOT / "certs" / "codesign.p12"
    
    if not cert_file.exists():
        print("INFO: No code signing certificate found. Skipping signature.")
        print("      To sign, place certificate at: certs/codesign.p12")
        return True
    
    exe_path = DIST_DIR / "PDFToolsDesktop.exe"
    if not exe_path.exists():
        print("WARNING: Executable not found for signing.")
        return False
    
    if sys.platform == "win32":
        # Windows code signing with signtool
        signtool = shutil.which("signtool")
        if signtool:
            cmd = [
                signtool, "sign",
                "/f", str(cert_file),
                "/tr", "http://timestamp.digicert.com",
                "/td", "sha256",
                "/fd", "sha256",
                str(exe_path)
            ]
            result = run_command(cmd, check=False)
            if result.returncode == 0:
                print("Executable signed successfully.")
                return True
            else:
                print(f"Signing failed: {result.stderr}")
                return False
        else:
            print("WARNING: signtool not found. Install Windows SDK for code signing.")
            return False
    
    else:
        print("INFO: Code signing configured for Windows only.")
        return True


def verify_build():
    """Verify the final build."""
    print("\n[6] Verifying build...")
    
    if sys.platform == "win32":
        exe_path = DIST_DIR / "PDFToolsDesktop.exe"
    elif sys.platform == "darwin":
        exe_path = DIST_DIR / "PDFToolsDesktop.app"
    else:
        exe_path = DIST_DIR / "PDFToolsDesktop"
    
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"✓ Build artifact: {exe_path}")
        print(f"  Size: {size_mb:.2f} MB")
        
        # Calculate SHA256 of the final executable
        sha256 = hashlib.sha256()
        with open(exe_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        print(f"  SHA256: {sha256.hexdigest()}")
        
        return True
    else:
        print(f"✗ Build artifact not found: {exe_path}")
        return False


def main():
    """Main build process."""
    print("=" * 60)
    print("PDF Tools Desktop - Obfuscated Build Script")
    print("=" * 60)
    
    # Check prerequisites
    if not check_pyarmor():
        return 1
    
    try:
        # Step 1: Generate integrity checksums
        generate_integrity_checksums()
        
        # Step 2: Obfuscate code
        if not obfuscate_code():
            return 1
        
        # Step 3: Copy assets
        copy_assets()
        
        # Step 4: Package
        if not package_with_pyinstaller():
            return 1
        
        # Step 5: Sign (optional)
        sign_executable()
        
        # Step 6: Verify
        if verify_build():
            print("\n" + "=" * 60)
            print("BUILD SUCCESSFUL!")
            print("=" * 60)
            print(f"Output: {DIST_DIR}")
            print("\nIMPORTANT:")
            print("1. The obfuscated executable contains anti-tampering measures")
            print("2. It will refuse to run if modified or debugged")
            print("3. Distribute this version to users")
            return 0
        else:
            print("\nBUILD VERIFICATION FAILED")
            return 1
    
    except Exception as e:
        print(f"\nBUILD ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
