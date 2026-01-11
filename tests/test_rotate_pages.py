import unittest
import os
from pikepdf import Pdf
from src.features.rotate_pages import rotate_pages

class TestRotatePages(unittest.TestCase):
    def setUp(self):
        # Create a dummy PDF file for testing
        self.test_dir = "test_pdfs"
        os.makedirs(self.test_dir, exist_ok=True)
        self.input_path = os.path.join(self.test_dir, "input.pdf")
        self.output_path = os.path.join(self.test_dir, "rotated.pdf")

        # Create a PDF with one page
        pdf = Pdf.new()
        pdf.add_blank_page()
        pdf.save(self.input_path)

    def tearDown(self):
        # Clean up the dummy files
        if os.path.exists(self.input_path):
            os.remove(self.input_path)
        if os.path.exists(self.output_path):
            os.remove(self.output_path)
        if os.path.isdir(self.test_dir) and not os.listdir(self.test_dir):
            os.rmdir(self.test_dir)

    def test_rotate_pages_valid(self):
        rotate_pages(self.input_path, self.output_path, 1, 90)
        self.assertTrue(os.path.exists(self.output_path))
        with Pdf.open(self.output_path) as rotated_pdf:
            self.assertEqual(rotated_pdf.pages[0].get("/Rotate"), 90)

    def test_rotate_pages_invalid_angle(self):
        with self.assertRaises(ValueError):
            rotate_pages(self.input_path, self.output_path, 1, 45)

    def test_rotate_pages_invalid_page(self):
        with self.assertRaises(ValueError):
            rotate_pages(self.input_path, self.output_path, 2, 90)

if __name__ == '__main__':
    unittest.main()
