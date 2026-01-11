import unittest
import os
from pikepdf import Pdf, PasswordError
from src.features.encrypt_pdf import encrypt_pdf

class TestEncryptPdf(unittest.TestCase):
    def setUp(self):
        # Create a dummy PDF file for testing
        self.test_dir = "test_pdfs"
        os.makedirs(self.test_dir, exist_ok=True)
        self.input_path = os.path.join(self.test_dir, "input.pdf")
        self.output_path = os.path.join(self.test_dir, "encrypted.pdf")

        # Create a PDF with one page
        pdf = Pdf.new()
        pdf.add_blank_page()
        pdf.save(self.input_path)
        
        self.permissions = {
            'print': True,
            'copy': True,
            'modify': False
        }

    def tearDown(self):
        # Clean up the dummy files
        if os.path.exists(self.input_path):
            os.remove(self.input_path)
        if os.path.exists(self.output_path):
            os.remove(self.output_path)
        os.rmdir(self.test_dir)

    def test_encrypt_pdf_user_password(self):
        encrypt_pdf(self.input_path, self.output_path, "user_pass", self.permissions, 128)
        self.assertTrue(os.path.exists(self.output_path))
        
        # Should be able to open with user password
        with Pdf.open(self.output_path, password="user_pass") as pdf:
            self.assertEqual(len(pdf.pages), 1)

        # Should NOT be able to open without password
        with self.assertRaises(PasswordError):
            Pdf.open(self.output_path)

    def test_encrypt_pdf_owner_password(self):
        encrypt_pdf(self.input_path, self.output_path, "user_pass", self.permissions, 128)
        self.assertTrue(os.path.exists(self.output_path))
        
        # Should be able to open with owner password
        with Pdf.open(self.output_path, password="user_pass") as pdf:
            self.assertEqual(len(pdf.pages), 1)
            self.assertTrue(pdf.owner_password_matched)


if __name__ == '__main__':
    unittest.main()