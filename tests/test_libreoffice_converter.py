import os
import sys
import unittest
from unittest.mock import patch, MagicMock

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

    @patch('src.utils.libreoffice_converter.subprocess.run')
    @patch('src.utils.libreoffice_converter.os.path.exists')
    @patch('src.utils.libreoffice_converter.tempfile.TemporaryDirectory')
    def test_convert_to_pptx(self, mock_temp_dir, mock_exists, mock_run):
        # Setup mocks
        mock_exists.side_effect = lambda path: True # All paths exist
        
        # Mock temp dir context manager
        mock_temp_obj = MagicMock()
        mock_temp_obj.__enter__.return_value = "C:\\Temp\\UserDir"
        mock_temp_dir.return_value = mock_temp_obj
        
        converter = LibreOfficeConverter()
        
        input_pdf = "C:\\Data\\test.pdf"
        output_dir = "C:\\Data"
        
        converter.convert_to_pptx(input_pdf, output_dir)
        
        # Verify subprocess call
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        cmd = args[0]
        
        self.assertIn("--headless", cmd)
        self.assertIn("--infilter=impress_pdf_import", cmd)
        self.assertIn('pptx:"Impress MS PowerPoint 2007 XML"', cmd)
        self.assertTrue(any(arg.startswith("-env:UserInstallation=") for arg in cmd))
        self.assertIn(output_dir, cmd)
        self.assertIn(input_pdf, cmd)

if __name__ == '__main__':
    unittest.main()
