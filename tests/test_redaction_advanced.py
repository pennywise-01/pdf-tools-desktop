import os
import pytest
import fitz
from src.features.redact_pdf import redact_pdf

@pytest.fixture
def sample_pdf(tmp_path):
    pdf_path = tmp_path / "test.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "This is a Secret document with ID:12345.")
    # Add a mixed case word to test case sensitivity
    page.insert_text((50, 80), "secret information.")
    doc.save(pdf_path)
    doc.close()
    return str(pdf_path)

def test_redact_numbers(sample_pdf, tmp_path):
    output_path = str(tmp_path / "redacted_nums.pdf")
    # Redact numbers only
    found = redact_pdf(sample_pdf, output_path, "", redact_numbers=True)
    assert found
    
    doc = fitz.open(output_path)
    text = doc[0].get_text()
    assert "ID:12345" not in text
    assert "12345" not in text
    assert "Secret" in text
    doc.close()

def test_redact_case_sensitive(sample_pdf, tmp_path):
    output_path = str(tmp_path / "redacted_case.pdf")
    # Redact "Secret" with match_case=True (Should NOT remove "secret")
    redact_pdf(sample_pdf, output_path, "Secret", match_case=True)
    
    doc = fitz.open(output_path)
    text = doc[0].get_text()
    assert "Secret" not in text
    assert "secret" in text
    doc.close()

def test_redact_case_insensitive(sample_pdf, tmp_path):
    output_path = str(tmp_path / "redacted_nocase.pdf")
    # Redact "Secret" with match_case=False (Should remove "Secret" and "secret")
    redact_pdf(sample_pdf, output_path, "Secret", match_case=False)
    
    doc = fitz.open(output_path)
    text = doc[0].get_text()
    assert "Secret" not in text
    assert "secret" not in text
    doc.close()

def test_preview_mode(sample_pdf, tmp_path):
    output_path = str(tmp_path / "preview.pdf")
    # Preview mode should NOT remove text, only highlight (which we can't easily check via get_text, but we check text remains)
    redact_pdf(sample_pdf, output_path, "Secret", preview_mode=True)
    
    doc = fitz.open(output_path)
    text = doc[0].get_text()
    assert "Secret" in text # Text should still exist underlying
    
    # Check for annotations
    # Keep page alive!
    page = doc[0]
    annots_list = list(page.annots())
    assert len(annots_list) > 0

    # Check if we have a Highlight annotation (type 8 in PDF spec/PyMuPDF)
    has_highlight = False
    for a in annots_list:
        # Accessing type safely
        try:
            # Newer PyMuPDF: type is property [int, str]
            t = a.type
            if isinstance(t, (list, tuple)):
                if t[0] == 8: has_highlight = True
            elif t == 8:
                has_highlight = True
        except:
            pass
            
    assert has_highlight, "Should have highlight annotation"
    doc.close()
