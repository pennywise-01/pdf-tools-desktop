import os
import sys
import logging

import fitz

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from features import pdf_to_pptx
from features import ocr_pdf as ocr_module
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


def test_find_libreoffice_supports_malformed_portable_folder_name(monkeypatch):
    malformed_dir = "LibreOfficePortableLibreOfficePortable"
    expected_suffix = os.path.join(
        malformed_dir,
        "App",
        "libreoffice",
        "program",
        "soffice.exe",
    )

    monkeypatch.setattr(pdf_to_pptx.os, "listdir", lambda _root: [malformed_dir])
    monkeypatch.setattr(pdf_to_pptx.os.path, "isdir", lambda path: path.endswith(malformed_dir))
    monkeypatch.setattr(pdf_to_pptx.shutil, "which", lambda _name: None)
    monkeypatch.setattr(
        pdf_to_pptx.os.path,
        "exists",
        lambda path: bool(path and path.endswith(expected_suffix)),
    )

    detected = pdf_to_pptx.find_libreoffice()
    assert detected is not None
    assert detected.endswith(expected_suffix)


def test_find_libreoffice_supports_env_override(monkeypatch):
    override = os.path.join("C:\\", "Custom", "LibreOffice", "program", "soffice.exe")
    monkeypatch.setenv("PDF_TOOLS_SOFFICE_PATH", override)
    monkeypatch.setattr(pdf_to_pptx.shutil, "which", lambda _name: None)
    monkeypatch.setattr(pdf_to_pptx.os.path, "exists", lambda path: path == os.path.normpath(override))

    detected = pdf_to_pptx.find_libreoffice()
    assert detected == os.path.abspath(os.path.normpath(override))


def test_convert_pdf_to_pptx_retries_when_first_success_is_invalid(monkeypatch, tmp_path):
    input_pdf = tmp_path / "input.pdf"
    output_pptx = tmp_path / "output.pptx"
    input_pdf.write_bytes(b"%PDF-1.4")

    call_order = []

    def _fake_libreoffice(_input_path, _output_path):
        call_order.append("libreoffice")
        return True, "Converted with LibreOffice"

    def _fake_custom(_input_path, _output_path):
        call_order.append("custom_engine")
        return True, "Converted with Enhanced Engine (Format Preserved)"

    monkeypatch.setattr(pdf_to_pptx, "pdf_has_extractable_text", lambda _path: True)
    monkeypatch.setattr(pdf_to_pptx, "pdf_has_visible_content", lambda _path: True)
    monkeypatch.setattr(pdf_to_pptx, "convert_with_libreoffice", _fake_libreoffice)
    monkeypatch.setattr(pdf_to_pptx, "convert_with_custom_engine", _fake_custom)
    monkeypatch.setattr(pdf_to_pptx, "convert_with_images", lambda *_: (False, "not needed"))

    validations = iter([(False, "corrupt package"), (True, "ok")])
    monkeypatch.setattr(pdf_to_pptx, "_validate_pptx_output", lambda _path, **_kwargs: next(validations))

    events = []
    monkeypatch.setattr(pdf_to_pptx.audit_logger, "log_event", lambda event, payload: events.append((event, payload)))

    success, message = pdf_to_pptx.convert_pdf_to_pptx(str(input_pdf), str(output_pptx))

    assert success is True
    assert "Enhanced Engine" in message
    assert call_order == ["libreoffice", "custom_engine"]
    assert events
    assert events[0][1]["method"] == "custom_engine"


def test_convert_pdf_to_pptx_uses_ocr_prepass_for_scanned_pdf(monkeypatch, tmp_path):
    input_pdf = tmp_path / "scanned.pdf"
    output_pptx = tmp_path / "output.pptx"
    input_pdf.write_bytes(b"%PDF-1.4")

    def _fake_ocr(_input_path, output_path, language="eng", progress_callback=None):
        _ = language
        _ = progress_callback
        with open(output_path, "wb") as f:
            f.write(b"%PDF-1.4 OCR")

    captured_inputs = []

    def _fake_libreoffice(conversion_input, _output_path):
        captured_inputs.append(conversion_input)
        return True, "Converted with LibreOffice"

    monkeypatch.setattr(pdf_to_pptx, "pdf_has_extractable_text", lambda _path: False)
    monkeypatch.setattr(pdf_to_pptx, "pdf_has_visible_content", lambda _path: True)
    monkeypatch.setattr(ocr_module, "setup_tesseract", lambda: True)
    monkeypatch.setattr(ocr_module, "ocr_pdf", _fake_ocr)
    monkeypatch.setattr(pdf_to_pptx, "convert_with_libreoffice", _fake_libreoffice)
    monkeypatch.setattr(pdf_to_pptx, "_validate_pptx_output", lambda _path, **_kwargs: (True, "ok"))
    monkeypatch.setattr(pdf_to_pptx.audit_logger, "log_event", lambda *_: None)

    success, message = pdf_to_pptx.convert_pdf_to_pptx(str(input_pdf), str(output_pptx))

    assert success is True
    assert captured_inputs
    assert captured_inputs[0] != str(input_pdf)
    assert "OCR pre-pass completed" in message


def test_convert_pdf_to_pptx_scanned_without_tesseract_uses_image_fallback(monkeypatch, tmp_path):
    input_pdf = tmp_path / "scanned-no-ocr.pdf"
    output_pptx = tmp_path / "output.pptx"
    input_pdf.write_bytes(b"%PDF-1.4")

    monkeypatch.setattr(pdf_to_pptx, "pdf_has_extractable_text", lambda _path: False)
    monkeypatch.setattr(pdf_to_pptx, "pdf_has_visible_content", lambda _path: True)
    monkeypatch.setattr(ocr_module, "setup_tesseract", lambda: False)
    monkeypatch.setattr(pdf_to_pptx, "convert_with_libreoffice", lambda *_: (False, "LibreOffice not found"))
    monkeypatch.setattr(pdf_to_pptx, "convert_with_custom_engine", lambda *_: (False, "Custom engine failed"))
    monkeypatch.setattr(pdf_to_pptx, "convert_with_images", lambda *_: (True, "Converted using high-quality images"))
    monkeypatch.setattr(pdf_to_pptx, "_validate_pptx_output", lambda _path, **_kwargs: (True, "ok"))

    events = []
    monkeypatch.setattr(pdf_to_pptx.audit_logger, "log_event", lambda event, payload: events.append((event, payload)))

    success, message = pdf_to_pptx.convert_pdf_to_pptx(str(input_pdf), str(output_pptx))

    assert success is True
    assert "Run OCR first" in message
    assert "fallback engine was used" in message
    assert events
    assert events[0][1]["method"] == "image"


def test_convert_pdf_to_pptx_does_not_require_content_for_blank_source(monkeypatch, tmp_path):
    input_pdf = tmp_path / "blank.pdf"
    output_pptx = tmp_path / "output.pptx"
    input_pdf.write_bytes(b"%PDF-1.4")

    validation_flags = []

    monkeypatch.setattr(pdf_to_pptx, "pdf_has_extractable_text", lambda _path: False)
    monkeypatch.setattr(pdf_to_pptx, "pdf_has_visible_content", lambda _path: False)
    monkeypatch.setattr(pdf_to_pptx, "convert_with_libreoffice", lambda *_: (True, "Converted with LibreOffice"))

    def _fake_validate(_path, **kwargs):
        validation_flags.append(kwargs.get("require_meaningful_content"))
        return True, "ok"

    monkeypatch.setattr(pdf_to_pptx, "_validate_pptx_output", _fake_validate)
    monkeypatch.setattr(pdf_to_pptx.audit_logger, "log_event", lambda *_: None)

    success, _message = pdf_to_pptx.convert_pdf_to_pptx(str(input_pdf), str(output_pptx))

    assert success is True
    assert validation_flags
    assert validation_flags[0] is False


def test_convert_pdf_to_pptx_prioritizes_image_when_libreoffice_export_unreliable(monkeypatch, tmp_path):
    input_pdf = tmp_path / "problematic.pdf"
    output_pptx = tmp_path / "output.pptx"
    input_pdf.write_bytes(b"%PDF-1.4")

    call_order = []

    def _fake_libreoffice(_input_path, _output_path):
        call_order.append("libreoffice")
        return False, "LibreOffice conversion failed: LibreOffice did not produce an output PPTX file."

    def _fake_image(_input_path, _output_path):
        call_order.append("image")
        return True, "Converted using high-quality images"

    def _fake_custom(_input_path, _output_path):
        call_order.append("custom_engine")
        return True, "Converted with Enhanced Engine (Format Preserved)"

    monkeypatch.setattr(pdf_to_pptx, "pdf_has_extractable_text", lambda _path: True)
    monkeypatch.setattr(pdf_to_pptx, "pdf_has_visible_content", lambda _path: True)
    monkeypatch.setattr(pdf_to_pptx, "convert_with_libreoffice", _fake_libreoffice)
    monkeypatch.setattr(pdf_to_pptx, "convert_with_images", _fake_image)
    monkeypatch.setattr(pdf_to_pptx, "convert_with_custom_engine", _fake_custom)
    monkeypatch.setattr(pdf_to_pptx, "_validate_pptx_output", lambda _path, **_kwargs: (True, "ok"))

    events = []
    monkeypatch.setattr(pdf_to_pptx.audit_logger, "log_event", lambda event, payload: events.append((event, payload)))

    success, message = pdf_to_pptx.convert_pdf_to_pptx(str(input_pdf), str(output_pptx))

    assert success is True
    assert "Visual fallback was prioritized" in message
    assert call_order == ["libreoffice", "image"]
    assert events
    assert events[0][1]["method"] == "image"


def test_convert_pdf_to_pptx_uses_pdftoppt_when_enabled(monkeypatch, tmp_path):
    input_pdf = tmp_path / "problematic.pdf"
    output_pptx = tmp_path / "output.pptx"
    input_pdf.write_bytes(b"%PDF-1.4")

    call_order = []
    captured_thresholds = []

    def _fake_libreoffice(_input_path, _output_path):
        call_order.append("libreoffice")
        return False, "LibreOffice not found"

    def _fake_pdftoppt(_input_path, _output_path, warning_threshold=None):
        call_order.append("pdftoppt")
        captured_thresholds.append(warning_threshold)
        return True, "Converted with pdftoppt experimental engine (warnings=0, line_warnings=0)"

    monkeypatch.setattr(pdf_to_pptx, "pdf_has_extractable_text", lambda _path: True)
    monkeypatch.setattr(pdf_to_pptx, "pdf_has_visible_content", lambda _path: True)
    monkeypatch.setattr(pdf_to_pptx, "convert_with_libreoffice", _fake_libreoffice)
    monkeypatch.setattr(pdf_to_pptx, "convert_with_pdftoppt", _fake_pdftoppt)
    monkeypatch.setattr(pdf_to_pptx, "convert_with_custom_engine", lambda *_: (False, "not needed"))
    monkeypatch.setattr(pdf_to_pptx, "convert_with_images", lambda *_: (False, "not needed"))
    monkeypatch.setattr(pdf_to_pptx, "HAS_PDFTOPPT", True)
    monkeypatch.setattr(pdf_to_pptx, "_validate_pptx_output", lambda _path, **_kwargs: (True, "ok"))

    events = []
    monkeypatch.setattr(pdf_to_pptx.audit_logger, "log_event", lambda event, payload: events.append((event, payload)))

    success, message = pdf_to_pptx.convert_pdf_to_pptx(
        str(input_pdf),
        str(output_pptx),
        enable_pdftoppt=True,
        pdftoppt_warning_threshold=77,
    )

    assert success is True
    assert call_order == ["pdftoppt"]
    assert captured_thresholds == [77]
    assert "pdftoppt" in message.lower()
    assert events
    assert events[0][1]["method"] == "pdftoppt"


def test_convert_pdf_to_pptx_falls_back_when_pdftoppt_warning_threshold_exceeded(monkeypatch, tmp_path):
    input_pdf = tmp_path / "problematic.pdf"
    output_pptx = tmp_path / "output.pptx"
    input_pdf.write_bytes(b"%PDF-1.4")

    call_order = []

    def _fake_libreoffice(_input_path, _output_path):
        call_order.append("libreoffice")
        return False, "LibreOffice not found"

    def _fake_pdftoppt(_input_path, _output_path, warning_threshold=None):
        call_order.append("pdftoppt")
        _ = warning_threshold
        return False, "pdftoppt warning threshold exceeded (350>200; line warnings=300)."

    def _fake_custom(_input_path, _output_path):
        call_order.append("custom_engine")
        return True, "Converted with Enhanced Engine (Format Preserved)"

    monkeypatch.setattr(pdf_to_pptx, "pdf_has_extractable_text", lambda _path: True)
    monkeypatch.setattr(pdf_to_pptx, "pdf_has_visible_content", lambda _path: True)
    monkeypatch.setattr(pdf_to_pptx, "convert_with_libreoffice", _fake_libreoffice)
    monkeypatch.setattr(pdf_to_pptx, "convert_with_pdftoppt", _fake_pdftoppt)
    monkeypatch.setattr(pdf_to_pptx, "convert_with_custom_engine", _fake_custom)
    monkeypatch.setattr(pdf_to_pptx, "convert_with_images", lambda *_: (False, "not needed"))
    monkeypatch.setattr(pdf_to_pptx, "HAS_PDFTOPPT", True)
    monkeypatch.setattr(pdf_to_pptx, "_validate_pptx_output", lambda _path, **_kwargs: (True, "ok"))

    events = []
    monkeypatch.setattr(pdf_to_pptx.audit_logger, "log_event", lambda event, payload: events.append((event, payload)))

    success, message = pdf_to_pptx.convert_pdf_to_pptx(
        str(input_pdf),
        str(output_pptx),
        enable_pdftoppt=True,
        pdftoppt_warning_threshold=200,
    )

    assert success is True
    assert call_order == ["pdftoppt", "libreoffice", "custom_engine"]
    assert "warning count exceeded" in message.lower()
    assert events
    assert events[0][1]["method"] == "custom_engine"


def test_convert_with_pdftoppt_line_warnings_are_non_fatal_by_default(monkeypatch, tmp_path):
    output_pptx = tmp_path / "pdftoppt.pptx"

    class _FakeConverter:
        def convert(self, _input_path, target_path):
            with open(target_path, "wb") as f:
                f.write(b"placeholder")
            logging.getLogger("pdftoppt.converter").warning(
                "Could not add element of type line: synthetic warning"
            )

    monkeypatch.setattr(pdf_to_pptx, "HAS_PDFTOPPT", True)
    monkeypatch.setattr(pdf_to_pptx, "AdvancedPDFToPowerPointConverter", _FakeConverter)

    success, message = pdf_to_pptx.convert_with_pdftoppt(
        "input.pdf",
        str(output_pptx),
        warning_threshold=0,
    )

    assert success is True
    assert "line_warnings=1" in message
    assert output_pptx.exists()


def test_convert_with_pdftoppt_enforces_threshold_for_non_line_warnings(monkeypatch, tmp_path):
    output_pptx = tmp_path / "pdftoppt_non_line.pptx"

    class _FakeConverter:
        def convert(self, _input_path, target_path):
            with open(target_path, "wb") as f:
                f.write(b"placeholder")
            logging.getLogger("pdftoppt.converter").warning(
                "Could not process vector object: synthetic warning"
            )

    monkeypatch.setattr(pdf_to_pptx, "HAS_PDFTOPPT", True)
    monkeypatch.setattr(pdf_to_pptx, "AdvancedPDFToPowerPointConverter", _FakeConverter)

    success, message = pdf_to_pptx.convert_with_pdftoppt(
        "input.pdf",
        str(output_pptx),
        warning_threshold=0,
    )

    assert success is False
    assert "threshold exceeded" in message.lower()
    assert not output_pptx.exists()
