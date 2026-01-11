import unittest
import os
from pikepdf import Pdf
from src.features.merge_pdf import merge_pdfs

class TestMergePdf(unittest.TestCase):
    def setUp(self):
        # Create dummy PDF files for testing
        self.test_dir = "test_pdfs"
        os.makedirs(self.test_dir, exist_ok=True)
        self.pdf1_path = os.path.join(self.test_dir, "pdf1.pdf")
        self.pdf2_path = os.path.join(self.test_dir, "pdf2.pdf")
        self.output_path = os.path.join(self.test_dir, "merged.pdf")

        # Create pdf1
        pdf1 = Pdf.new()
        pdf1.add_blank_page()
        pdf1.save(self.pdf1_path)

        # Create pdf2
        pdf2 = Pdf.new()
        pdf2.add_blank_page()
        pdf2.add_blank_page()
        pdf2.save(self.pdf2_path)

        self.pdf_files = [self.pdf1_path, self.pdf2_path]

    def tearDown(self):
        # Clean up the dummy files
        for file in self.pdf_files:
            os.remove(file)
        if os.path.exists(self.output_path):
            os.remove(self.output_path)
        os.rmdir(self.test_dir)

    def test_merge_pdfs(self):
        merge_pdfs(self.pdf_files, self.output_path)
        self.assertTrue(os.path.exists(self.output_path))
        with Pdf.open(self.output_path) as merged_pdf:
            self.assertEqual(len(merged_pdf.pages), 3)

if __name__ == '__main__':
    unittest.main()
