"""
Anti-Tampering Module for PDF Tools Desktop
Implements security measures to protect against:
- Code modification/tampering
- Debugging attempts
- Virtual machine analysis
"""

import hashlib
import os
import sys
import platform
import ctypes
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import json


class TamperingDetectedError(Exception):
    """Raised when tampering is detected."""
    pass


class IntegrityChecker:
    """
    Verifies the integrity of core application files using SHA-256 checksums.
    Calculates checksums on startup and compares against expected values.
    """
    
    def __init__(self, base_path: Optional[str] = None):
        self.base_path = base_path or self._get_base_path()
        self.checksum_file = os.path.join(self.base_path, '.integrity_checksums.json')
        
    def _get_base_path(self) -> str:
        """Get the base path for the application."""
        if getattr(sys, 'frozen', False):
            # Running as compiled executable (PyInstaller)
            return os.path.dirname(sys.executable)
        else:
            # Running as script
            return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of a file."""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception:
            return ''
    
    def get_core_files(self) -> List[str]:
        """Get list of core files to check for integrity."""
        core_files = []
        
        if getattr(sys, 'frozen', False):
            # For compiled executable, check the executable itself
            core_files.append(sys.executable)
        else:
            # For development, check source files
            source_patterns = [
                'main.py',
                'network_security.py',
                'license_public_keys.json',
                'features/*.py',
                'tabs/*.py',
                'utils/*.py',
                'widgets/*.py',
            ]
            
            for pattern in source_patterns:
                full_pattern = os.path.join(self.base_path, 'src', pattern)
                import glob
                core_files.extend(glob.glob(full_pattern))
        
        return [f for f in core_files if os.path.isfile(f)]
    
    def generate_checksums(self) -> Dict[str, str]:
        """Generate checksums for all core files."""
        checksums = {}
        for file_path in self.get_core_files():
            relative_path = os.path.relpath(file_path, self.base_path)
            checksums[relative_path] = self._calculate_file_hash(file_path)
        return checksums
    
    def save_checksums(self, checksums: Optional[Dict[str, str]] = None) -> None:
        """Save checksums to file (used during build process)."""
        if checksums is None:
            checksums = self.generate_checksums()
        
        with open(self.checksum_file, 'w') as f:
            json.dump(checksums, f, indent=2)
    
    def load_checksums(self) -> Dict[str, str]:
        """Load expected checksums from file."""
        try:
            with open(self.checksum_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def verify_integrity(self) -> Tuple[bool, List[str]]:
        """
        Verify integrity of core files.
        Returns (is_valid, list_of_issues)
        """
        expected_checksums = self.load_checksums()
        
        # If no checksums file exists, generate one (first run or development)
        if not expected_checksums:
            if not getattr(sys, 'frozen', False):
                # In development mode, just save current checksums
                self.save_checksums()
                return True, []
            else:
                # In production, this is a problem
                return False, ["Integrity checksums file not found"]
        
        issues = []
        current_checksums = self.generate_checksums()
        
        # Check for modified files
        for file_path, expected_hash in expected_checksums.items():
            current_hash = current_checksums.get(file_path)
            if current_hash is None:
                issues.append(f"Missing file: {file_path}")
            elif current_hash != expected_hash:
                issues.append(f"Modified file: {file_path}")
        
        # Check for added files (only in production)
        if getattr(sys, 'frozen', False):
            for file_path in current_checksums:
                if file_path not in expected_checksums:
                    issues.append(f"Unexpected file: {file_path}")
        
        return len(issues) == 0, issues


class AntiDebug:
    """
    Anti-debugging and anti-analysis measures.
    Detects common debugging tools and virtualized environments.
    """
    
    # Known debugger process names
    DEBUGGER_PROCESSES = [
        'ollydbg.exe', 'x64dbg.exe', 'x32dbg.exe', 'idaq.exe', 'idaq64.exe',
        'idag.exe', 'idag64.exe', 'ida.exe', 'ida64.exe', 'windbg.exe',
        'immunitydebugger.exe', 'gdb.exe', 'lldb.exe', 'radare2.exe',
        'cutter.exe', 'ghidra.exe', 'cheatengine.exe', 'cheat engine.exe',
        'processhacker.exe', 'procmon.exe', 'procexp.exe', 'procexp64.exe',
        'tcpview.exe', 'autoruns.exe', 'filemon.exe', 'regmon.exe',
        'vboxservice.exe', 'vboxtray.exe', 'vmwaretray.exe', 'vmwareuser.exe',
        'vmtoolsd.exe', 'vmacthlp.exe', 'fakenet.exe', 'apimonitor.exe',
        'apispy.exe', 'spyxx.exe', 'spyxx_amd64.exe', 'detours.exe',
        'syser.exe', 'softice.exe', 'iceext.exe', 'joeboxcontrol.exe',
        'joeboxserver.exe', 'sandboxiedcomlaunch.exe', 'sandboxierpcss.exe',
        'analysis.exec', 'wireshark.exe', 'fiddler.exe', 'charles.exe',
        'burpsuite.exe', 'ollyice.exe', 'softice.exe', 'symefw.exe',
    ]
    
    # Known VM artifacts
    VM_INDICATORS = [
        # VMware
        'vmware', 'virtual hd', 'vmware virtual',
        # VirtualBox
        'vbox', 'virtualbox', 'oracle corporation',
        # Hyper-V
        'microsoft corporation hyper-v', 'hyper-v',
        # Parallels
        'parallels', 'parallels software',
        # Xen
        'xen', 'hvm domu',
        # QEMU
        'qemu', 'bochs',
    ]
    
    @classmethod
    def is_debugger_present(cls) -> bool:
        """Check if a debugger is attached to the process."""
        if sys.platform == 'win32':
            try:
                kernel32 = ctypes.windll.kernel32
                return kernel32.IsDebuggerPresent() != 0
            except Exception:
                pass
        return False
    
    @classmethod
    def check_debugger_processes(cls) -> List[str]:
        """Check for known debugger processes running on the system."""
        detected = []
        
        try:
            if sys.platform == 'win32':
                import subprocess
                result = subprocess.run(
                    ['tasklist', '/fo', 'csv', '/nh'],
                    capture_output=True, text=True, timeout=5
                )
                process_list = result.stdout.lower()
                
                for debugger in cls.DEBUGGER_PROCESSES:
                    if debugger.lower() in process_list:
                        detected.append(debugger)
        except Exception:
            pass
        
        return detected
    
    @classmethod
    def detect_vm_artifacts(cls) -> List[str]:
        """Detect virtual machine artifacts."""
        indicators = []
        
        try:
            # Check CPU info
            if sys.platform == 'win32':
                import subprocess
                
                # Check CPU name
                try:
                    result = subprocess.run(
                        ['wmic', 'cpu', 'get', 'name'],
                        capture_output=True, text=True, timeout=5
                    )
                    cpu_name = result.stdout.lower()
                    for indicator in cls.VM_INDICATORS:
                        if indicator in cpu_name:
                            indicators.append(f"CPU: {indicator}")
                except Exception:
                    pass
                
                # Check BIOS info
                try:
                    result = subprocess.run(
                        ['wmic', 'bios', 'get', 'manufacturer'],
                        capture_output=True, text=True, timeout=5
                    )
                    bios_manufacturer = result.stdout.lower()
                    for indicator in cls.VM_INDICATORS:
                        if indicator in bios_manufacturer:
                            indicators.append(f"BIOS: {indicator}")
                except Exception:
                    pass
                
                # Check disk drives
                try:
                    result = subprocess.run(
                        ['wmic', 'diskdrive', 'get', 'model'],
                        capture_output=True, text=True, timeout=5
                    )
                    disk_models = result.stdout.lower()
                    for indicator in cls.VM_INDICATORS:
                        if indicator in disk_models:
                            indicators.append(f"Disk: {indicator}")
                except Exception:
                    pass
                
                # Check for VM-specific processes
                try:
                    result = subprocess.run(
                        ['tasklist', '/fo', 'csv', '/nh'],
                        capture_output=True, text=True, timeout=5
                    )
                    process_list = result.stdout.lower()
                    
                    vm_processes = [
                        'vboxservice.exe', 'vboxtray.exe',
                        'vmwaretray.exe', 'vmwareuser.exe',
                        'vmtoolsd.exe', 'vmacthlp.exe'
                    ]
                    for vm_proc in vm_processes:
                        if vm_proc in process_list:
                            indicators.append(f"Process: {vm_proc}")
                except Exception:
                    pass
            
            elif sys.platform == 'darwin':
                # macOS checks
                import subprocess
                
                # Check system profiler for VM indicators
                try:
                    result = subprocess.run(
                        ['system_profiler', 'SPHardwareDataType'],
                        capture_output=True, text=True, timeout=10
                    )
                    hardware_info = result.stdout.lower()
                    
                    vm_keywords = ['vmware', 'virtualbox', 'parallels']
                    for keyword in vm_keywords:
                        if keyword in hardware_info:
                            indicators.append(f"macOS Hardware: {keyword}")
                except Exception:
                    pass
            
            else:
                # Linux checks
                try:
                    # Check for hypervisor in CPU info
                    with open('/proc/cpuinfo', 'r') as f:
                        cpuinfo = f.read().lower()
                        if 'hypervisor' in cpuinfo:
                            indicators.append("Linux: Hypervisor detected in CPU info")
                except Exception:
                    pass
                
                try:
                    # Check DMI product name
                    if os.path.exists('/sys/class/dmi/id/product_name'):
                        with open('/sys/class/dmi/id/product_name', 'r') as f:
                            product_name = f.read().lower()
                            for indicator in cls.VM_INDICATORS:
                                if indicator in product_name:
                                    indicators.append(f"DMI Product: {indicator}")
                except Exception:
                    pass
                
                try:
                    # Check for systemd-detect-virt
                    result = subprocess.run(
                        ['systemd-detect-virt'],
                        capture_output=True, text=True, timeout=5
                    )
                    if result.returncode == 0 and result.stdout.strip() != 'none':
                        indicators.append(f"systemd-detect-virt: {result.stdout.strip()}")
                except Exception:
                    pass
        
        except Exception:
            pass
        
        return indicators
    
    @classmethod
    def detect_debug_registers(cls) -> bool:
        """Check if hardware debug registers are being used."""
        if sys.platform == 'win32':
            try:
                # Check if hardware breakpoints are set
                import ctypes
                from ctypes import wintypes
                
                class CONTEXT(ctypes.Structure):
                    _fields_ = [
                        ("ContextFlags", wintypes.DWORD),
                        ("Dr0", wintypes.ULONG_PTR),
                        ("Dr1", wintypes.ULONG_PTR),
                        ("Dr2", wintypes.ULONG_PTR),
                        ("Dr3", wintypes.ULONG_PTR),
                        ("Dr6", wintypes.ULONG_PTR),
                        ("Dr7", wintypes.ULONG_PTR),
                    ]
                
                # Get thread context
                kernel32 = ctypes.windll.kernel32
                GetCurrentThread = kernel32.GetCurrentThread
                GetCurrentThread.restype = wintypes.HANDLE
                
                thread = GetCurrentThread()
                context = CONTEXT()
                context.ContextFlags = 0x00010010  # CONTEXT_DEBUG_REGISTERS
                
                if kernel32.GetThreadContext(thread, ctypes.byref(context)):
                    # Check if any debug registers are set
                    if context.Dr0 or context.Dr1 or context.Dr2 or context.Dr3:
                        return True
            except Exception:
                pass
        
        return False
    
    @classmethod
    def timing_check(cls, threshold_ms: float = 100.0) -> bool:
        """
        Check execution timing to detect debugger single-stepping.
        Returns True if timing anomaly detected (possible debugging).
        """
        import time
        
        # Simple timing check
        start = time.perf_counter()
        
        # Perform some operations
        for i in range(100000):
            _ = i * i
        
        elapsed_ms = (time.perf_counter() - start) * 1000
        
        # If execution took significantly longer than expected, might be debugged
        return elapsed_ms > threshold_ms * 10
    
    @classmethod
    def run_all_checks(cls) -> Tuple[bool, Dict[str, any]]:
        """
        Run all anti-debug checks.
        Returns (is_safe, details_dict)
        """
        results = {
            'debugger_present': cls.is_debugger_present(),
            'debugger_processes': cls.check_debugger_processes(),
            'vm_indicators': cls.detect_vm_artifacts(),
            'debug_registers': cls.detect_debug_registers(),
            'timing_anomaly': cls.timing_check(),
        }
        
        # Determine if safe (no debugger detected)
        is_safe = (
            not results['debugger_present'] and
            len(results['debugger_processes']) == 0 and
            not results['timing_anomaly']
            # Note: VM detection alone doesn't block - just flagged
        )
        
        return is_safe, results


def verify_application_integrity(exit_on_failure: bool = True) -> bool:
    """
    Main entry point for integrity verification.
    Should be called early in application startup.
    """
    checker = IntegrityChecker()
    is_valid, issues = checker.verify_integrity()
    
    if not is_valid:
        error_msg = "Application integrity check failed:\n" + "\n".join(issues)
        print(f"SECURITY ALERT: {error_msg}", file=sys.stderr)
        
        if exit_on_failure:
            sys.exit(1)
        return False
    
    return True


def verify_no_debugging(exit_on_detection: bool = True) -> bool:
    """
    Main entry point for anti-debug checks.
    Should be called early in application startup.
    """
    is_safe, results = AntiDebug.run_all_checks()
    
    if not is_safe:
        details = []
        if results['debugger_present']:
            details.append("Debugger detected (IsDebuggerPresent)")
        if results['debugger_processes']:
            details.append(f"Debugger processes: {', '.join(results['debugger_processes'])}")
        if results['debug_registers']:
            details.append("Hardware breakpoints detected")
        if results['timing_anomaly']:
            details.append("Timing anomaly detected (possible single-stepping)")
        
        error_msg = "Debugging/analysis tools detected:\n" + "\n".join(details)
        print(f"SECURITY ALERT: {error_msg}", file=sys.stderr)
        
        if exit_on_detection:
            sys.exit(1)
        return False
    
    # Log VM detection (informational only)
    if results['vm_indicators']:
        print(f"INFO: VM environment detected: {', '.join(results['vm_indicators'])}")
    
    return True


def initialize_security(exit_on_failure: bool = True) -> bool:
    """
    Initialize all anti-tampering security measures.
    Call this at the very beginning of main.py.
    """
    try:
        # Check integrity first
        if not verify_application_integrity(exit_on_failure=exit_on_failure):
            return False
        
        # Check for debugging
        if not verify_no_debugging(exit_on_detection=exit_on_failure):
            return False
        
        print("Security: Anti-tampering checks passed.")
        return True
    
    except Exception as e:
        print(f"Security: Error during anti-tampering checks: {e}", file=sys.stderr)
        if exit_on_failure:
            sys.exit(1)
        return False


if __name__ == '__main__':
    # Test the module
    print("Testing Anti-Tampering Module...")
    print("=" * 50)
    
    # Test integrity checker
    print("\n[1] Integrity Checker Test")
    checker = IntegrityChecker()
    print(f"Base path: {checker.base_path}")
    print(f"Checksum file: {checker.checksum_file}")
    
    # Generate checksums
    print("\nGenerating checksums...")
    checksums = checker.generate_checksums()
    print(f"Generated {len(checksums)} checksums")
    for path, hash_val in list(checksums.items())[:5]:
        print(f"  {path}: {hash_val[:16]}...")
    
    # Save and verify
    checker.save_checksums(checksums)
    is_valid, issues = checker.verify_integrity()
    print(f"\nIntegrity check: {'PASSED' if is_valid else 'FAILED'}")
    if issues:
        for issue in issues:
            print(f"  Issue: {issue}")
    
    # Test anti-debug
    print("\n[2] Anti-Debug Test")
    print(f"Debugger present: {AntiDebug.is_debugger_present()}")
    print(f"Debug registers: {AntiDebug.detect_debug_registers()}")
    print(f"Debugger processes: {AntiDebug.check_debugger_processes()}")
    print(f"VM indicators: {AntiDebug.detect_vm_artifacts()}")
    print(f"Timing anomaly: {AntiDebug.timing_check()}")
    
    # Run all checks
    print("\n[3] Running all checks...")
    is_safe, results = AntiDebug.run_all_checks()
    print(f"Overall safety: {'SAFE' if is_safe else 'UNSAFE'}")
    print(f"Detailed results: {json.dumps(results, indent=2)}")
