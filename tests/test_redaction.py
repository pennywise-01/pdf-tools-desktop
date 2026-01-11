import os
import pytest
import fitz
from src.features.redact_pdf import redact_pdf

@pytest.fixture
def sample_pdf(tmp_path):
    pdf_path = tmp_path / "test.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "This is a secret document with some confidential info and private data.")
    doc.save(pdf_path)
    doc.close()
    return str(pdf_path)

def test_redact_single_word(sample_pdf, tmp_path):
    output_path = str(tmp_path / "redacted_single.pdf")
    redact_pdf(sample_pdf, output_path, "secret")
    
    doc = fitz.open(output_path)
    text = doc[0].get_text()
    assert "secret" not in text
    assert "confidential" in text
    doc.close()

def test_redact_multiple_words(sample_pdf, tmp_path):
    output_path = str(tmp_path / "redacted_multi.pdf")
    redact_pdf(sample_pdf, output_path, "secret, confidential, private")
    
    doc = fitz.open(output_path)
    text = doc[0].get_text()
    assert "secret" not in text
    assert "confidential" not in text
    assert "private" not in text
    assert "document" in text # Check text that shouldn't be redacted
    doc.close()
