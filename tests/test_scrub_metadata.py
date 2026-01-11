import unittest
import os
from pikepdf import Pdf
from src.features.scrub_metadata import scrub_metadata

class TestScrubMetadata(unittest.TestCase):
    def setUp(self):
        # Create a dummy PDF file for testing
        self.test_dir = "test_pdfs"
        os.makedirs(self.test_dir, exist_ok=True)
        self.input_path = os.path.join(self.test_dir, "input.pdf")
        self.output_path = os.path.join(self.test_dir, "scrubbed.pdf")

        # Create a PDF with metadata
        pdf = Pdf.new()
        pdf.add_blank_page()
        with pdf.open_metadata() as meta:
            meta["dc:title"] = "My test PDF"
            meta["dc:creator"] = "Test Script"
        pdf.save(self.input_path)

    def tearDown(self):
        # Clean up the dummy files
        if os.path.exists(self.input_path):
            os.remove(self.input_path)
        if os.path.exists(self.output_path):
            os.remove(self.output_path)
        if os.path.isdir(self.test_dir) and not os.listdir(self.test_dir):
            os.rmdir(self.test_dir)

    def test_scrub_metadata(self):
        scrub_metadata(self.input_path, self.output_path)
        self.assertTrue(os.path.exists(self.output_path))
        with Pdf.open(self.output_path) as scrubbed_pdf:
            with self.assertRaises(KeyError):
                scrubbed_pdf.docinfo["/Title"]
            with self.assertRaises(KeyError):
                scrubbed_pdf.docinfo["/Author"]

if __name__ == '__main__':
    unittest.main()
