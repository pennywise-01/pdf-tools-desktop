"""
Tests for the anti-tampering module.
These tests verify integrity checking and anti-debug functionality.
"""

import pytest
import os
import sys
import json
import tempfile
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.anti_tampering import (
    IntegrityChecker,
    AntiDebug,
    TamperingDetectedError,
    verify_application_integrity,
    verify_no_debugging,
    initialize_security
)


class TestIntegrityChecker:
    """Tests for the integrity checking functionality."""
    
    def test_calculate_file_hash(self, tmp_path):
        """Test SHA-256 hash calculation."""
        checker = IntegrityChecker()
        
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)
        
        # Calculate hash
        hash_result = checker._calculate_file_hash(str(test_file))
        
        # Verify against known hash
        expected_hash = hashlib.sha256(test_content).hexdigest()
        assert hash_result == expected_hash
    
    def test_calculate_hash_missing_file(self, tmp_path):
        """Test hash calculation for non-existent file."""
        checker = IntegrityChecker()
        
        hash_result = checker._calculate_file_hash(str(tmp_path / "nonexistent.txt"))
        assert hash_result == ''
    
    def test_save_and_load_checksums(self, tmp_path):
        """Test saving and loading checksums."""
        checker = IntegrityChecker(str(tmp_path))
        
        # Create test checksums
        test_checksums = {
            "file1.py": "abc123",
            "file2.py": "def456"
        }
        
        # Save
        checker.save_checksums(test_checksums)
        
        # Verify file exists
        assert (tmp_path / ".integrity_checksums.json").exists()
        
        # Load and verify
        loaded = checker.load_checksums()
        assert loaded == test_checksums
    
    def test_verify_integrity_success(self, tmp_path):
        """Test integrity verification with valid files."""
        checker = IntegrityChecker(str(tmp_path))
        
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        # Calculate hash and save
        file_hash = checker._calculate_file_hash(str(test_file))
        relative_path = os.path.relpath(str(test_file), str(tmp_path))
        
        test_checksums = {relative_path: file_hash}
        checker.save_checksums(test_checksums)
        
        # Verify integrity by loading the checksum and comparing
        loaded_checksums = checker.load_checksums()
        current_hash = checker._calculate_file_hash(str(test_file))
        
        assert loaded_checksums[relative_path] == current_hash
    
    def test_verify_integrity_modified_file(self, tmp_path):
        """Test detection of modified files."""
        checker = IntegrityChecker(str(tmp_path))
        
        # Create and hash a file
        test_file = tmp_path / "test.txt"
        test_file.write_text("original content")
        
        # Save the original hash
        relative_path = os.path.relpath(str(test_file), str(tmp_path))
        original_hash = checker._calculate_file_hash(str(test_file))
        test_checksums = {relative_path: original_hash}
        checker.save_checksums(test_checksums)
        
        # Modify the file
        test_file.write_text("modified content")
        
        # Verify - should detect modification
        loaded_checksums = checker.load_checksums()
        current_hash = checker._calculate_file_hash(str(test_file))
        
        assert relative_path in loaded_checksums
        assert loaded_checksums[relative_path] != current_hash
    
    def test_verify_integrity_missing_file(self, tmp_path):
        """Test detection of missing files."""
        # Create source directory
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        
        # Create and hash a file
        test_file = src_dir / "test.py"
        test_file.write_text("content")
        
        checker = IntegrityChecker(str(tmp_path))
        
        # Manually create checksums for the test file
        test_checksums = {
            "src/test.py": checker._calculate_file_hash(str(test_file))
        }
        checker.save_checksums(test_checksums)
        
        # Delete the file
        test_file.unlink()
        
        # Verify - should detect missing file
        is_valid, issues = checker.verify_integrity()
        assert is_valid is False
        assert any("Missing file" in issue for issue in issues)
    
    def test_load_checksums_missing_file(self, tmp_path):
        """Test loading when checksums file doesn't exist."""
        checker = IntegrityChecker(str(tmp_path))
        
        loaded = checker.load_checksums()
        assert loaded == {}


class TestAntiDebug:
    """Tests for anti-debugging functionality."""
    
    def test_is_debugger_present(self):
        """Test debugger detection (should pass in test environment)."""
        # This test just ensures the method doesn't crash
        result = AntiDebug.is_debugger_present()
        assert isinstance(result, bool)
    
    def test_detect_debug_registers(self):
        """Test debug register detection."""
        # This test just ensures the method doesn't crash
        result = AntiDebug.detect_debug_registers()
        assert isinstance(result, bool)
    
    def test_check_debugger_processes_returns_list(self):
        """Test that process check returns a list."""
        processes = AntiDebug.check_debugger_processes()
        assert isinstance(processes, list)
    
    def test_detect_vm_artifacts_returns_list(self):
        """Test that VM detection returns a list."""
        indicators = AntiDebug.detect_vm_artifacts()
        assert isinstance(indicators, list)
    
    def test_timing_check_returns_bool(self):
        """Test timing check returns boolean."""
        result = AntiDebug.timing_check(threshold_ms=1000.0)
        assert isinstance(result, bool)
    
    def test_run_all_checks_structure(self):
        """Test that run_all_checks returns expected structure."""
        is_safe, results = AntiDebug.run_all_checks()
        
        assert isinstance(is_safe, bool)
        assert isinstance(results, dict)
        assert 'debugger_present' in results
        assert 'debugger_processes' in results
        assert 'vm_indicators' in results
        assert 'debug_registers' in results
        assert 'timing_anomaly' in results


class TestIntegrationFunctions:
    """Tests for the main integration functions."""
    
    @patch('utils.anti_tampering.IntegrityChecker')
    def test_verify_application_integrity_success(self, mock_checker_class, tmp_path):
        """Test successful integrity verification."""
        mock_checker = MagicMock()
        mock_checker.verify_integrity.return_value = (True, [])
        mock_checker_class.return_value = mock_checker
        
        result = verify_application_integrity(exit_on_failure=False)
        assert result is True
    
    @patch('utils.anti_tampering.IntegrityChecker')
    def test_verify_application_integrity_failure(self, mock_checker_class, tmp_path):
        """Test failed integrity verification."""
        mock_checker = MagicMock()
        mock_checker.verify_integrity.return_value = (False, ["Modified file: test.py"])
        mock_checker_class.return_value = mock_checker
        
        result = verify_application_integrity(exit_on_failure=False)
        assert result is False
    
    @patch('utils.anti_tampering.AntiDebug')
    def test_verify_no_debugging_safe(self, mock_antidebug):
        """Test verification when no debugging detected."""
        mock_antidebug.run_all_checks.return_value = (True, {
            'debugger_present': False,
            'debugger_processes': [],
            'vm_indicators': [],
            'debug_registers': False,
            'timing_anomaly': False
        })
        
        result = verify_no_debugging(exit_on_detection=False)
        assert result is True
    
    @patch('utils.anti_tampering.AntiDebug')
    def test_verify_no_debugging_detected(self, mock_antidebug):
        """Test verification when debugging is detected."""
        mock_antidebug.run_all_checks.return_value = (False, {
            'debugger_present': True,
            'debugger_processes': ['ollydbg.exe'],
            'vm_indicators': [],
            'debug_registers': False,
            'timing_anomaly': False
        })
        
        result = verify_no_debugging(exit_on_detection=False)
        assert result is False
    
    @patch('utils.anti_tampering.verify_application_integrity')
    @patch('utils.anti_tampering.verify_no_debugging')
    def test_initialize_security_success(self, mock_verify_debug, mock_verify_integrity):
        """Test successful security initialization."""
        mock_verify_integrity.return_value = True
        mock_verify_debug.return_value = True
        
        result = initialize_security(exit_on_failure=False)
        assert result is True
    
    @patch('utils.anti_tampering.verify_application_integrity')
    def test_initialize_security_integrity_fail(self, mock_verify_integrity):
        """Test security initialization when integrity check fails."""
        mock_verify_integrity.return_value = False
        
        result = initialize_security(exit_on_failure=False)
        assert result is False


class TestModuleExecution:
    """Tests for when the module is run directly."""
    
    def test_module_imports(self):
        """Test that the module can be imported."""
        import utils.anti_tampering as at
        
        assert hasattr(at, 'IntegrityChecker')
        assert hasattr(at, 'AntiDebug')
        assert hasattr(at, 'verify_application_integrity')
        assert hasattr(at, 'verify_no_debugging')
        assert hasattr(at, 'initialize_security')
        assert hasattr(at, 'TamperingDetectedError')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
