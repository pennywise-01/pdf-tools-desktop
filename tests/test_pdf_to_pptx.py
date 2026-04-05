import os
import sys

import fitz

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from features import pdf_to_pptx
from features.pdf_to_pptx import pdf_has_extractable_text, _finalize_success_message


def test_pdf_has_extractable_text_true(tmp_path):
    pdf_path = tmp_path / "text.pdf"

    with fitz.open() as doc:
        page = doc.new_page(width=595, height=842)
        page.insert_text((72, 100), "Hello editable world", fontsize=18)
        doc.save(str(pdf_path))

    assert pdf_has_extractable_text(str(pdf_path)) is True


def test_pdf_has_extractable_text_false_for_blank_page(tmp_path):
    pdf_path = tmp_path / "blank.pdf"

    with fitz.open() as doc:
        _ = doc.new_page(width=595, height=842)
        doc.save(str(pdf_path))

    assert pdf_has_extractable_text(str(pdf_path)) is False


def test_finalize_success_message_adds_scanned_hint_when_no_text():
    msg = _finalize_success_message("Converted with LibreOffice", source_has_text=False, method="libreoffice")
    assert "image-only/scanned" in msg
    assert "Run OCR first" in msg


def test_finalize_success_message_adds_image_fallback_hint_when_text_exists():
    msg = _finalize_success_message("Converted using high-quality images", source_has_text=True, method="image")
    assert "fell back to image-based slides" in msg


def test_find_libreoffice_supports_nested_portable_layout(monkeypatch):
    expected_suffix = os.path.join(
        "LibreOfficePortable",
        "LibreOfficePortable",
        "App",
        "libreoffice",
        "program",
        "soffice.exe",
    )

    monkeypatch.setattr(pdf_to_pptx.shutil, "which", lambda _name: None)
    monkeypatch.setattr(
        pdf_to_pptx.os.path,
        "exists",
        lambda path: bool(path and path.endswith(expected_suffix)),
    )

    detected = pdf_to_pptx.find_libreoffice()
    assert detected is not None
    assert detected.endswith(expected_suffix)
