import unittest
import os
from pikepdf import Pdf
from src.features.split_pdf import split_pdf

class TestSplitPdf(unittest.TestCase):
    def setUp(self):
        # Create a dummy PDF file for testing
        self.test_dir = "test_pdfs"
        os.makedirs(self.test_dir, exist_ok=True)
        self.input_path = os.path.join(self.test_dir, "input.pdf")
        self.output_path = os.path.join(self.test_dir, "split.pdf")

        # Create a PDF with 15 pages
        pdf = Pdf.new()
        for _ in range(15):
            pdf.add_blank_page()
        pdf.save(self.input_path)

    def tearDown(self):
        # Clean up the dummy files
        if os.path.exists(self.input_path):
            os.remove(self.input_path)
        if os.path.exists(self.output_path):
            os.remove(self.output_path)
        os.rmdir(self.test_dir)

    def test_split_pdf_valid_range(self):
        split_pdf(self.input_path, self.output_path, "1-5, 8, 11-15")
        self.assertTrue(os.path.exists(self.output_path))
        with Pdf.open(self.output_path) as split_pdf_file:
            self.assertEqual(len(split_pdf_file.pages), 11)

    def test_split_pdf_single_pages(self):
        split_pdf(self.input_path, self.output_path, "1, 3, 5")
        self.assertTrue(os.path.exists(self.output_path))
        with Pdf.open(self.output_path) as split_pdf_file:
            self.assertEqual(len(split_pdf_file.pages), 3)

    def test_split_pdf_invalid_range(self):
        with self.assertRaises(ValueError):
            split_pdf(self.input_path, self.output_path, "1-20") # Out of bounds
        with self.assertRaises(ValueError):
            split_pdf(self.input_path, self.output_path, "10-5") # Invalid range

if __name__ == '__main__':
    unittest.main()
