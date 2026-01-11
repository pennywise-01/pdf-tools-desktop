import os
import pytest
import fitz
from src.features.watermark import add_watermark
from src.features.compress_pdf import compress_pdf
from src.features.redact_pdf import redact_pdf
from src.features.shred_file import shred_file

@pytest.fixture
def sample_pdf(tmp_path):
    pdf_path = tmp_path / "test.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "This is a secret document.")
    doc.save(pdf_path)
    doc.close()
    return str(pdf_path)

def test_watermark(sample_pdf, tmp_path):
    output_path = str(tmp_path / "watermarked.pdf")
    add_watermark(sample_pdf, output_path, "CONFIDENTIAL", opacity=0.5, rotation=45)
    
    assert os.path.exists(output_path)
    doc = fitz.open(output_path)
    # Check if text exists (simple check, extracting text might put watermark text at end)
    text = doc[0].get_text()
    assert "CONFIDENTIAL" in text
    doc.close()

def test_compress_pdf(sample_pdf, tmp_path):
    output_path = str(tmp_path / "compressed.pdf")
    # Since sample is tiny, compression might not actually reduce size much, but we test it runs
    compress_pdf(sample_pdf, output_path, quality=4)
    assert os.path.exists(output_path)
    
    doc = fitz.open(output_path)
    assert doc.page_count == 1
    doc.close()

def test_redact_pdf(sample_pdf, tmp_path):
    output_path = str(tmp_path / "redacted.pdf")
    redact_pdf(sample_pdf, output_path, "secret")
    
    assert os.path.exists(output_path)
    doc = fitz.open(output_path)
    text = doc[0].get_text()
    assert "secret" not in text
    assert "This is a" in text # Remaining text
    doc.close()

def test_shred_file(tmp_path):
    # Create a dummy file to shred
    file_to_shred = tmp_path / "shred_me.txt"
    file_to_shred.write_text("Delete me")
    file_path = str(file_to_shred)
    
    assert os.path.exists(file_path)
    shred_file(file_path, passes=1) # 1 pass for speed in test
    
    assert not os.path.exists(file_path)
