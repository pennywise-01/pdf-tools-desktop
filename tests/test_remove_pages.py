import unittest
import os
from pikepdf import Pdf
from src.features.remove_pages import remove_pages

class TestRemovePages(unittest.TestCase):
    def setUp(self):
        # Create a dummy PDF file for testing
        self.test_dir = "test_pdfs"
        os.makedirs(self.test_dir, exist_ok=True)
        self.input_path = os.path.join(self.test_dir, "input.pdf")
        self.output_path = os.path.join(self.test_dir, "removed.pdf")

        # Create a PDF with 10 pages
        pdf = Pdf.new()
        for _ in range(10):
            pdf.add_blank_page()
        pdf.save(self.input_path)

    def tearDown(self):
        # Clean up the dummy files
        if os.path.exists(self.input_path):
            os.remove(self.input_path)
        if os.path.exists(self.output_path):
            os.remove(self.output_path)
        os.rmdir(self.test_dir)

    def test_remove_pages_valid(self):
        remove_pages(self.input_path, self.output_path, "1, 3, 5")
        self.assertTrue(os.path.exists(self.output_path))
        with Pdf.open(self.output_path) as removed_pdf:
            self.assertEqual(len(removed_pdf.pages), 7)

    def test_remove_pages_invalid(self):
        with self.assertRaises(ValueError):
            remove_pages(self.input_path, self.output_path, "1, 11") # Out of bounds

if __name__ == '__main__':
    unittest.main()
