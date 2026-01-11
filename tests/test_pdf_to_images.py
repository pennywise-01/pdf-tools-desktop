import os
import pytest
import fitz
from src.features.pdf_to_images import convert_pdf_to_images

@pytest.fixture
def create_dummy_pdf(tmp_path):
    pdf_path = tmp_path / "test.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Hello, World!")
    doc.save(str(pdf_path))
    doc.close()
    return str(pdf_path)

def test_convert_pdf_to_images(create_dummy_pdf, tmp_path):
    output_dir = tmp_path / "images"
    images = convert_pdf_to_images(create_dummy_pdf, str(output_dir), dpi=72)
    
    assert os.path.exists(output_dir)
    assert len(images) == 1
    assert os.path.exists(images[0])
    assert images[0].endswith(".png")
