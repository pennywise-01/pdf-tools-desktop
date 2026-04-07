import os
import sys
import unittest
from unittest.mock import patch
from subprocess import CompletedProcess

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.libreoffice_converter import LibreOfficeConverter

class TestLibreOfficeConverter(unittest.TestCase):
    
    @patch('src.utils.libreoffice_converter.os.path.exists')
    def test_find_soffice_success(self, mock_exists):
        # Setup mock to return True when checking for soffice.exe
        # We need to handle the side_effect carefully because the constructor calls _find_soffice
        
        # We want to simulate that the file exists at the expected path
        def side_effect(path):
            if path.endswith("soffice.exe"):
                return True
            return False
            
        mock_exists.side_effect = side_effect
        
        converter = LibreOfficeConverter()
        self.assertIsNotNone(converter.soffice_path)
        self.assertTrue(converter.soffice_path.endswith("soffice.exe"))

    @patch('src.utils.libreoffice_converter.os.path.exists')
    def test_find_soffice_failure(self, mock_exists):
        # Simulate file not found
        mock_exists.return_value = False
        
        with self.assertRaises(FileNotFoundError):
            LibreOfficeConverter()

    @patch('src.utils.libreoffice_converter.shutil.which', return_value=None)
    @patch('src.utils.libreoffice_converter.os.listdir')
    @patch('src.utils.libreoffice_converter.os.path.isdir')
    @patch('src.utils.libreoffice_converter.os.path.exists')
    def test_find_soffice_supports_malformed_portable_folder(
        self,
        mock_exists,
        mock_isdir,
        mock_listdir,
        _mock_which,
    ):
        malformed_dir = "LibreOfficePortableLibreOfficePortable"
        expected_suffix = os.path.join(
            malformed_dir,
            "App",
            "libreoffice",
            "program",
            "soffice.exe",
        )

        mock_listdir.return_value = [malformed_dir]
        mock_isdir.side_effect = lambda path: path.endswith(malformed_dir)
        mock_exists.side_effect = lambda path: bool(path and path.endswith(expected_suffix))

        converter = LibreOfficeConverter()
        self.assertIsNotNone(converter.soffice_path)
        self.assertTrue(converter.soffice_path.endswith(expected_suffix))

    @patch('src.utils.libreoffice_converter.shutil.rmtree')
    @patch('src.utils.libreoffice_converter.subprocess.run')
    @patch('src.utils.libreoffice_converter.os.path.exists')
    @patch('src.utils.libreoffice_converter.tempfile.mkdtemp')
    def test_convert_to_pptx(self, mock_mkdtemp, mock_exists, mock_run, mock_rmtree):
        # Setup mocks
        mock_exists.side_effect = lambda path: True # All paths exist
        mock_mkdtemp.return_value = "C:\\Temp\\UserDir"
        
        converter = LibreOfficeConverter()
        
        input_pdf = "C:\\Data\\test.pdf"
        output_dir = "C:\\Data"
        
        converted_path = converter.convert_to_pptx(input_pdf, output_dir)
        
        # Verify subprocess call
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        cmd = args[0]
        
        self.assertIn("--headless", cmd)
        self.assertIn("--nologo", cmd)
        self.assertIn("--nodefault", cmd)
        self.assertIn("--norestore", cmd)
        self.assertIn("--infilter=impress_pdf_import", cmd)
        self.assertIn('pptx:"Impress MS PowerPoint 2007 XML"', cmd)
        self.assertTrue(any(arg.startswith("-env:UserInstallation=") for arg in cmd))
        self.assertIn(output_dir, cmd)
        self.assertIn(input_pdf, cmd)
        self.assertEqual(kwargs.get("timeout"), 300)
        self.assertTrue(converted_path.endswith("test.pptx"))
        mock_rmtree.assert_called_once_with("C:\\Temp\\UserDir", ignore_errors=True)

    @patch('src.utils.libreoffice_converter.shutil.rmtree')
    @patch('src.utils.libreoffice_converter.subprocess.run')
    @patch('src.utils.libreoffice_converter.os.path.exists')
    @patch('src.utils.libreoffice_converter.tempfile.mkdtemp')
    @patch.object(LibreOfficeConverter, '_find_generated_pptx')
    def test_convert_to_pptx_retries_when_no_output_detected(
        self,
        mock_find_generated,
        mock_mkdtemp,
        mock_exists,
        mock_run,
        mock_rmtree,
    ):
        mock_mkdtemp.return_value = "C:\\Temp\\UserDir"
        mock_exists.side_effect = lambda path: bool(path and path.endswith("soffice.exe")) or path in ["C:\\Data\\test.pdf", "C:\\Data"]

        mock_run.side_effect = [
            CompletedProcess(args=["soffice"], returncode=0, stdout="", stderr=""),
            CompletedProcess(args=["soffice"], returncode=0, stdout="", stderr=""),
        ]
        mock_find_generated.side_effect = [None, "C:\\Data\\fallback-name.pptx"]

        converter = LibreOfficeConverter()
        converted_path = converter.convert_to_pptx("C:\\Data\\test.pdf", "C:\\Data")

        self.assertEqual(mock_run.call_count, 2)
        self.assertTrue(converted_path.endswith("fallback-name.pptx"))
        mock_rmtree.assert_called_once_with("C:\\Temp\\UserDir", ignore_errors=True)

    @patch('src.utils.libreoffice_converter.shutil.rmtree')
    @patch('src.utils.libreoffice_converter.subprocess.run')
    @patch('src.utils.libreoffice_converter.os.path.exists')
    @patch('src.utils.libreoffice_converter.tempfile.mkdtemp')
    @patch.object(LibreOfficeConverter, '_find_generated_pptx')
    def test_convert_to_pptx_emits_debug_messages(
        self,
        mock_find_generated,
        mock_mkdtemp,
        mock_exists,
        mock_run,
        mock_rmtree,
    ):
        mock_mkdtemp.return_value = "C:\\Temp\\UserDir"
        mock_exists.side_effect = lambda path: bool(path and path.endswith("soffice.exe")) or path in ["C:\\Data\\test.pdf", "C:\\Data"]

        mock_run.side_effect = [
            CompletedProcess(args=["soffice"], returncode=0, stdout="", stderr=""),
            CompletedProcess(args=["soffice"], returncode=0, stdout="", stderr=""),
        ]
        mock_find_generated.side_effect = [None, "C:\\Data\\fallback-name.pptx"]

        logs = []
        converter = LibreOfficeConverter()
        _ = converter.convert_to_pptx("C:\\Data\\test.pdf", "C:\\Data", debug_logger=logs.append)

        self.assertGreaterEqual(len(logs), 2)
        self.assertTrue(any("attempt 1/3" in msg.lower() for msg in logs))
        self.assertTrue(any("successful" in msg.lower() for msg in logs))
        mock_rmtree.assert_called_once_with("C:\\Temp\\UserDir", ignore_errors=True)

    @patch('src.utils.libreoffice_converter.os.path.exists')
    def test_extract_pptx_path_from_stdout(self, mock_exists):
        mock_exists.side_effect = lambda path: bool(path and (path.endswith("soffice.exe") or path.endswith("test.pptx")))

        converter = LibreOfficeConverter()
        stdout_text = "convert C:/a/test.pdf -> C:/out/test.pptx using filter : Impress MS PowerPoint 2007 XML"
        parsed = converter._extract_pptx_path_from_stdout(stdout_text)

        self.assertIsNotNone(parsed)
        self.assertTrue(parsed.lower().endswith("test.pptx"))

if __name__ == '__main__':
    unittest.main()
