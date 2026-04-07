import fitz
import os
import sys
import subprocess
import tempfile
import shutil
import zipfile
import re
import logging
from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from utils.audit_log import audit_logger

# Try to import Aspose (commercial library with good PDF parsing)
try:
    import aspose.slides as slides
    HAS_ASPOSE = True
except ImportError:
    HAS_ASPOSE = False


# Try to import pdftoppt (experimental free converter with stronger editability)
try:
    from pdftoppt.converter import AdvancedPDFToPowerPointConverter
    HAS_PDFTOPPT = True
except Exception:
    AdvancedPDFToPowerPointConverter = None
    HAS_PDFTOPPT = False


class _PdftopptWarningCounter(logging.Handler):
    """Capture warning volume from pdftoppt loggers for fallback decisions."""

    def __init__(self):
        super().__init__(level=logging.WARNING)
        self.total_warnings = 0
        self.line_warnings = 0
        self.non_line_warnings = 0

    def emit(self, record):
        if record.levelno < logging.WARNING:
            return

        self.total_warnings += 1
        message = record.getMessage()
        if "could not add element of type line" in message.lower():
            self.line_warnings += 1
        else:
            self.non_line_warnings += 1


def _resolve_pdftoppt_warning_threshold(default_value=200):
    """Resolve warning threshold from environment with a safe default."""
    raw_value = os.environ.get("PDF_TOOLS_PDFTOPPT_WARNING_THRESHOLD", str(default_value)).strip()
    try:
        return max(0, int(raw_value))
    except Exception:
        return default_value


def _resolve_pdftoppt_line_warning_weight(default_value=0.0):
    """Resolve how much line-only warnings contribute to threshold checks."""
    raw_value = os.environ.get(
        "PDF_TOOLS_PDFTOPPT_LINE_WARNING_WEIGHT",
        str(default_value),
    ).strip()
    try:
        return max(0.0, float(raw_value))
    except Exception:
        return default_value


def _invoke_pdftoppt_converter(converter, input_path, output_path):
    """Invoke pdftoppt regardless of minor API naming differences between versions."""
    candidate_methods = [
        "convert",
        "convert_pdf_to_pptx",
        "convert_file",
    ]

    for method_name in candidate_methods:
        method = getattr(converter, method_name, None)
        if callable(method):
            method(input_path, output_path)
            return

    raise RuntimeError("Unsupported pdftoppt converter API.")


def pdf_has_extractable_text(input_path, sample_pages=3):
    """Return True when the PDF appears to contain an extractable text layer."""
    try:
        doc = fitz.open(input_path)
        page_count = min(len(doc), max(1, sample_pages))
        for index in range(page_count):
            text = doc[index].get_text("text")
            if text and text.strip():
                doc.close()
                return True
        doc.close()
        return False
    except Exception:
        # Fail open so conversion continues even if text inspection fails.
        return True


def pdf_has_visible_content(input_path, sample_pages=3):
    """Return True when sampled pages contain text, drawings, or images."""
    try:
        doc = fitz.open(input_path)
        page_count = min(len(doc), max(1, sample_pages))
        for index in range(page_count):
            page = doc[index]

            text = page.get_text("text")
            if text and text.strip():
                doc.close()
                return True

            if page.get_images(full=True):
                doc.close()
                return True

            if page.get_drawings():
                doc.close()
                return True

        doc.close()
        return False
    except Exception:
        # Fail open so fallback logic does not reject potentially valid output.
        return True


def _finalize_success_message(message, source_has_text, method):
    if not source_has_text:
        return (
            message
            + " Source PDF appears image-only/scanned, so slides may be non-editable. "
            + "Run OCR first if you need editable text."
        )

    if method == "image":
        return (
            message
            + " Editable text was not preserved because conversion fell back to image-based slides."
        )

    return message


def find_libreoffice():
    """Find LibreOffice installation path."""
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    possible_paths = []

    # Allow explicit override for portable or custom installations.
    env_override = os.environ.get("PDF_TOOLS_SOFFICE_PATH")
    if env_override:
        possible_paths.append(env_override)

    # Known workspace portable layouts.
    possible_paths.extend([
        os.path.join(project_root, "LibreOfficePortable", "App", "libreoffice", "program", "soffice.exe"),
        os.path.join(project_root, "LibreOfficePortable", "LibreOfficePortable", "App", "libreoffice", "program", "soffice.exe"),
    ])

    # Discover additional workspace folder variants, including malformed extraction names.
    try:
        for entry in os.listdir(project_root):
            entry_path = os.path.join(project_root, entry)
            if not os.path.isdir(entry_path):
                continue

            if "libreofficeportable" not in entry.lower():
                continue

            possible_paths.extend([
                os.path.join(entry_path, "App", "libreoffice", "program", "soffice.exe"),
                os.path.join(entry_path, "LibreOfficePortable", "App", "libreoffice", "program", "soffice.exe"),
            ])
    except Exception:
        pass

    possible_paths.extend([
        r"C:\LibreOffice\program\soffice.exe",
        r"C:\LibreOfficePortable\App\libreoffice\program\soffice.exe",
        r"C:\PortableApps\LibreOfficePortable\App\libreoffice\program\soffice.exe",
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        shutil.which("soffice"),
        shutil.which("libreoffice"),
    ])

    seen = set()
    for path in possible_paths:
        if not path:
            continue

        normalized = os.path.normpath(path)
        if normalized in seen:
            continue
        seen.add(normalized)

        if os.path.exists(normalized):
            return os.path.abspath(normalized)

    return None


def convert_with_aspose(input_path, output_path):
    """
    Convert PDF to PPTX using Aspose.Slides via a separate subprocess.
    This isolates any potential crashes (segfaults) in the C++ library.
    """
    if not HAS_ASPOSE:
        return False, "Aspose not installed"
    
    worker_script = os.path.join(os.path.dirname(__file__), "aspose_worker.py")
    
    try:
        # Run the worker script in a separate process
        # We use sys.executable to ensure we use the same Python interpreter
        cmd = [sys.executable, worker_script, input_path, output_path]
        
        # CREATE_NO_WINDOW flag for Windows to suppress console window popping up
        creationflags = 0x08000000 if sys.platform == "win32" else 0
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=creationflags
        )
        
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            return True, "Converted with Aspose (editable text preserved)"
        elif process.returncode == 2:
             return False, "Aspose.Slides python package is not installed correctly."
        else:
             # Process failed (crashed or exception)
             error_msg = stderr.strip() if stderr else "Unknown error occurred in conversion process"
             if not error_msg and process.returncode != 0:
                 error_msg = f"Process crashed with exit code {process.returncode}"
             return False, f"Aspose conversion failed: {error_msg}"

    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, f"Failed to launch conversion process: {str(e)}"


def convert_with_libreoffice(input_path, output_path):
    """
    Convert PDF to PPTX using the hardened LibreOffice wrapper.
    """
    try:
        from utils.libreoffice_converter import LibreOfficeConverter
        converter = LibreOfficeConverter()
    except FileNotFoundError:
        return False, "LibreOffice not found"

    temp_dir = tempfile.mkdtemp()
    try:
        converted_path = converter.convert_to_pptx(
            input_path,
            output_dir=temp_dir,
            timeout=300,
            debug_logger=log_debug,
        )
        if os.path.abspath(converted_path) != os.path.abspath(output_path):
            if os.path.exists(output_path):
                os.remove(output_path)
            shutil.move(converted_path, output_path)

        return True, "Converted with LibreOffice"
    except Exception as e:
        return False, f"LibreOffice conversion failed: {str(e)}"
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def convert_with_pdftoppt(input_path, output_path, warning_threshold=None):
    """
    Convert using pdftoppt (experimental editable path).
    Can enforce warning_threshold for automatic fallback.
    """
    if not HAS_PDFTOPPT:
        return False, "pdftoppt package is not installed"

    warning_counter = _PdftopptWarningCounter()
    pdftoppt_logger = logging.getLogger("pdftoppt.converter")
    previous_level = pdftoppt_logger.level
    pdftoppt_logger.addHandler(warning_counter)

    if pdftoppt_logger.level > logging.WARNING:
        pdftoppt_logger.setLevel(logging.WARNING)

    try:
        converter = AdvancedPDFToPowerPointConverter()
        _invoke_pdftoppt_converter(converter, input_path, output_path)
    except Exception as e:
        return False, f"pdftoppt conversion failed: {str(e)}"
    finally:
        pdftoppt_logger.removeHandler(warning_counter)
        pdftoppt_logger.setLevel(previous_level)

    line_warning_weight = _resolve_pdftoppt_line_warning_weight()
    effective_warning_score = (
        warning_counter.non_line_warnings
        + (warning_counter.line_warnings * line_warning_weight)
    )

    warning_summary = (
        f"warnings={warning_counter.total_warnings}, "
        f"actionable_warnings={warning_counter.non_line_warnings}, "
        f"line_warnings={warning_counter.line_warnings}, "
        f"effective_warning_score={effective_warning_score:.2f}, "
        f"line_warning_weight={line_warning_weight:g}"
    )

    if warning_threshold is not None and effective_warning_score > warning_threshold:
        _remove_file_safely(output_path)
        return (
            False,
            (
                "pdftoppt warning threshold exceeded "
                f"(effective {effective_warning_score:.2f}>{warning_threshold}; "
                f"actionable warnings={warning_counter.non_line_warnings}; "
                f"line warnings={warning_counter.line_warnings}; "
                f"line warning weight={line_warning_weight:g})."
            ),
        )

    return True, f"Converted with pdftoppt experimental engine ({warning_summary})"


def _remove_file_safely(path):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


def _pptx_has_meaningful_content(output_path):
    """Detect whether a PPTX contains text, images, or drawable content."""
    try:
        with zipfile.ZipFile(output_path, "r") as archive:
            slide_xml_files = sorted(
                [
                    name
                    for name in archive.namelist()
                    if name.startswith("ppt/slides/slide") and name.endswith(".xml")
                ]
            )

            for slide_xml_file in slide_xml_files:
                xml_text = archive.read(slide_xml_file).decode("utf-8", errors="ignore")

                if "<p:pic" in xml_text or "<a:blipFill" in xml_text:
                    return True
                if "<p:graphicFrame" in xml_text:
                    return True
                if "<p:cxnSp" in xml_text or "<p:grpSp" in xml_text:
                    return True

                text_runs = re.findall(r"<a:t>(.*?)</a:t>", xml_text, flags=re.DOTALL)
                if any(text.strip() for text in text_runs):
                    return True

                # Treat non-placeholder shapes as meaningful visual content.
                if "<p:sp " in xml_text and "<p:ph" not in xml_text:
                    return True

        return False
    except Exception:
        return False


def _validate_pptx_output(output_path, min_size_bytes=2048, require_meaningful_content=False):
    """Validate the generated PPTX before declaring conversion success."""
    if not os.path.exists(output_path):
        return False, "Output PPTX file was not created."

    try:
        size = os.path.getsize(output_path)
    except OSError as e:
        return False, f"Cannot read output size: {e}"

    if size < min_size_bytes:
        return False, f"Output PPTX file is too small ({size} bytes)."

    try:
        with zipfile.ZipFile(output_path, "r") as archive:
            members = set(archive.namelist())
            if "[Content_Types].xml" not in members:
                return False, "Missing [Content_Types].xml in PPTX package."
            if "ppt/presentation.xml" not in members:
                return False, "Missing ppt/presentation.xml in PPTX package."
            if archive.testzip() is not None:
                return False, "Corrupted PPTX zip content detected."
    except Exception as e:
        return False, f"Output is not a valid PPTX archive: {e}"

    try:
        presentation = Presentation(output_path)
        if len(presentation.slides) == 0:
            return False, "Output PPTX contains zero slides."
    except Exception as e:
        return False, f"PPTX cannot be opened by python-pptx: {e}"

    if require_meaningful_content and not _pptx_has_meaningful_content(output_path):
        return False, "Output PPTX appears blank (no text, pictures, or drawable content detected)."

    return True, "ok"


def _maybe_ocr_prepass(input_path):
    """
    Attempt OCR pre-pass for scanned PDFs to improve editable text extraction.
    Returns (working_input_path, cleanup_temp_pdf_path, note).
    """
    try:
        from features.ocr_pdf import ocr_pdf, setup_tesseract
    except Exception as exc:
        return input_path, None, f"OCR pre-pass unavailable: {exc}"

    if not setup_tesseract():
        return input_path, None, "Tesseract OCR is not available; continuing without OCR pre-pass."

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    ocr_path = tmp.name
    tmp.close()

    try:
        ocr_pdf(input_path, ocr_path, language="eng")
        if not os.path.exists(ocr_path) or os.path.getsize(ocr_path) == 0:
            _remove_file_safely(ocr_path)
            return input_path, None, "OCR pre-pass did not produce a usable file; continuing with original PDF."

        return ocr_path, ocr_path, "OCR pre-pass completed to improve editable text extraction."
    except Exception as exc:
        _remove_file_safely(ocr_path)
        return input_path, None, f"OCR pre-pass failed: {exc}"


def _run_conversion_method(
    method_name,
    method_func,
    input_path,
    output_path,
    require_meaningful_content=False,
):
    """Execute a conversion method and validate its output."""
    _remove_file_safely(output_path)
    success, message = method_func(input_path, output_path)
    if not success:
        return False, message

    is_valid, validation_message = _validate_pptx_output(
        output_path,
        require_meaningful_content=require_meaningful_content,
    )
    if not is_valid:
        _remove_file_safely(output_path)
        return False, f"{message}. Output validation failed: {validation_message}"

    return True, message


def _should_prioritize_visual_fallback(libreoffice_error_message):
    """
    Identify LibreOffice failures where image fallback should be preferred
    over custom reconstruction for better visual fidelity.
    """
    message = (libreoffice_error_message or "").lower()
    trigger_phrases = [
        "did not produce an output pptx file",
        "winerror 32",
        "being used by another process",
        "parser error",
        "please verify input parameters",
        "conversion failed",
    ]
    return any(phrase in message for phrase in trigger_phrases)


def convert_with_images(input_path, output_path):
    """
    Fallback: Convert PDF to PPTX using high-resolution images.
    Perfect visual fidelity but text is not editable.
    """
    doc = fitz.open(input_path)
    prs = Presentation()
    blank_slide_layout = prs.slide_layouts[6]
    temp_dir = tempfile.mkdtemp()
    
    for page_num, page in enumerate(doc):
        width_pt = page.rect.width
        height_pt = page.rect.height
        prs.slide_width = Emu(int(width_pt * 12700))
        prs.slide_height = Emu(int(height_pt * 12700))
        
        slide = prs.slides.add_slide(blank_slide_layout)
        
        # Render at 300 DPI for high quality
        zoom = 300 / 72
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        
        img_path = os.path.join(temp_dir, f"page_{page_num}.png")
        pix.save(img_path)
        
        slide.shapes.add_picture(
            img_path,
            Emu(0),
            Emu(0),
            width=prs.slide_width,
            height=prs.slide_height
        )
    
    doc.close()
    prs.save(output_path)
    
    # Clean up
    for f in os.listdir(temp_dir):
        try:
            os.remove(os.path.join(temp_dir, f))
        except:
            pass
    try:
        os.rmdir(temp_dir)
    except:
        pass
    
    return True, "Converted using high-quality images (formatting preserved)"



def _rgb_from_int(color_int):
    """Convert integer color to RGBColor object safely."""
    try:
        r = (color_int >> 16) & 0xFF
        g = (color_int >> 8) & 0xFF
        b = color_int & 0xFF
        return RGBColor(r, g, b)
    except:
        return RGBColor(0, 0, 0)

def _rgb_from_seq(color_seq):
    """Convert float sequence (0.0-1.0) to RGBColor object."""
    if not color_seq or len(color_seq) < 3:
        return None
    try:
        return RGBColor(
            int(color_seq[0] * 255),
            int(color_seq[1] * 255),
            int(color_seq[2] * 255)
        )
    except:
        return None

def convert_with_custom_engine(input_path, output_path):
    """
    Convert using precise layout reconstruction with PyMuPDF and python-pptx.
    Reconstructs the PDF by analyzing text blocks, images, and vector graphics
    and placing them onto PowerPoint slides at their exact coordinates.
    """
    try:
        doc = fitz.open(input_path)
        prs = Presentation()
        
        # Set slide dimensions based on the first page
        if len(doc) > 0:
            first_page = doc[0]
            prs.slide_width = Emu(int(first_page.rect.width * 12700))
            prs.slide_height = Emu(int(first_page.rect.height * 12700))

        # Blank layout
        blank_slide_layout = prs.slide_layouts[6] 

        for page in doc:
            slide = prs.slides.add_slide(blank_slide_layout)
            
            # 1. Process Vector Graphics (Backgrounds, Shapes, Lines)
            # This captures tables borders, backgrounds, underlines, etc.
            drawings = page.get_drawings()
            for shape in drawings:
                rect = shape["rect"]
                # Convert fitz rect to pptx size/pos
                x, y = rect.x0, rect.y0
                w, h = rect.width, rect.height
                
                # Filter out tiny shapes that might be artifacts
                if w < 1 and h < 1:
                    continue
                
                # Determine fill and line color
                fill_color = _rgb_from_seq(shape.get("fill"))
                line_color = _rgb_from_seq(shape.get("color"))
                
                # Check items to guess shape type
                # Simple approximation: rectangles are common for backgrounds
                is_rect = False
                for item in shape["items"]:
                    if item[0] == "re":
                        is_rect = True
                        break
                
                try:
                    ppt_shape = None
                    if is_rect:
                        ppt_shape = slide.shapes.add_shape(
                            MSO_SHAPE.RECTANGLE, 
                            Pt(x), Pt(y), Pt(w), Pt(h)
                        )
                    elif w > 0 and h > 0: 
                        # Fallback for non-rect shapes (just bounding box rect for now)
                        # A better implementation would use FreeformBuilder for paths
                        pass 
                    
                    if ppt_shape:
                        # Apply formatting
                        if fill_color:
                            ppt_shape.fill.solid()
                            ppt_shape.fill.fore_color.rgb = fill_color
                        else:
                            ppt_shape.fill.background() # No fill
                        
                        if line_color:
                            ppt_shape.line.color.rgb = line_color
                            ppt_shape.line.width = Pt(shape.get("width", 1))
                        else:
                            ppt_shape.line.fill.background() # No line
                except Exception:
                    pass

            # 2. Process Text and Images
            # flags=fitz.TEXT_PRESERVE_LIGATURES | WHITE | IMAGES
            blocks = page.get_text("dict", flags=11)["blocks"]

            for block in blocks:
                bbox = block["bbox"]
                x, y = bbox[0], bbox[1]
                w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
                
                if w <= 0 or h <= 0: continue

                if block["type"] == 0:  # Text Block
                    try:
                        # Slight adjustment to prevent text wrapping issues
                        # PPTX text boxes differ slightly in padding
                        txBox = slide.shapes.add_textbox(Pt(x), Pt(y), Pt(w + 2), Pt(h + 2))
                        tf = txBox.text_frame
                        tf.word_wrap = True 

                        for line in block["lines"]:
                            p = tf.add_paragraph()
                            # Try to preserve alignment if possible
                            # PyMuPDF doesn't give alignment safely, but we can assume separate blocks usually mean separate alignment logic
                            
                            for span in line["spans"]:
                                run = p.add_run()
                                run.text = span["text"]
                                
                                # Font size
                                try:
                                    run.font.size = Pt(max(6, span["size"]))
                                except:
                                    pass

                                # Font family mapping
                                fname = span["font"].lower()
                                if "times" in fname:
                                    run.font.name = "Times New Roman"
                                elif "courier" in fname:
                                    run.font.name = "Courier New"
                                elif "arial" in fname or "helvetica" in fname:
                                    run.font.name = "Arial"
                                else:
                                    run.font.name = "Calibri"

                                # Styling
                                flags = span.get("flags", 0)
                                if flags & 2**4: run.font.bold = True
                                if flags & 2**1: run.font.italic = True

                                # Color
                                run.font.color.rgb = _rgb_from_int(span["color"])
                                
                    except Exception:
                        pass 

                elif block["type"] == 1:  # Image Block
                    image_bytes = block.get("image")
                    ext = block.get("ext", "png")
                    if image_bytes:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp_img:
                            tmp_img.write(image_bytes)
                            tmp_img_path = tmp_img.name
                        
                        try:
                            slide.shapes.add_picture(tmp_img_path, Pt(x), Pt(y), width=Pt(w), height=Pt(h))
                        except Exception:
                            pass
                        finally:
                            if os.path.exists(tmp_img_path):
                                try: os.remove(tmp_img_path)
                                except: pass

        doc.close()
        prs.save(output_path)
        return True, "Converted with Enhanced Engine (Format Preserved)"

    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, f"Custom engine error: {str(e)}"




def log_debug(message):
    try:
        debug_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "debug_conversion.txt")
        with open(debug_file, "a") as f:
            f.write(f"{message}\n")
    except:
        pass

def convert_pdf_to_pptx(
    input_path,
    output_path,
    enable_pdftoppt=None,
    pdftoppt_warning_threshold=None,
):
    """
    Convert PDF to PowerPoint (PPTX).
    
    Strategy:
    1. Try LibreOffice conversion
    2. Optionally try pdftoppt experimental editable conversion
    3. Try custom engine reconstruction
    4. Fallback to image-based slides
    5. Optionally allow Aspose when PDF_TOOLS_ENABLE_ASPOSE=1
    """
    log_debug(f"\n--- Starting conversion for {input_path} ---")
    ocr_temp_path = None
    try:
        method_errors = {}
        pdftoppt_warning_skipped = False
        pdftoppt_unavailable = False
        pdftoppt_attempted = False
        pdftoppt_failure_message = ""
        source_has_text = pdf_has_extractable_text(input_path)
        source_has_visible_content = pdf_has_visible_content(input_path)
        log_debug(f"Source has extractable text: {source_has_text}")
        log_debug(f"Source has visible content: {source_has_visible_content}")

        working_input_path = input_path
        ocr_note = ""
        effective_has_text = source_has_text
        if not source_has_text:
            log_debug("Source appears scanned/image-only. Attempting OCR pre-pass...")
            working_input_path, ocr_temp_path, ocr_note = _maybe_ocr_prepass(input_path)
            log_debug(ocr_note)
            if ocr_temp_path:
                effective_has_text = True

        if enable_pdftoppt is None:
            enable_pdftoppt = os.environ.get("PDF_TOOLS_ENABLE_PDFTOPPT", "0") == "1"

        if pdftoppt_warning_threshold is None:
            pdftoppt_warning_threshold = _resolve_pdftoppt_warning_threshold()

        log_debug(f"Experimental pdftoppt enabled: {enable_pdftoppt}")
        if enable_pdftoppt:
            log_debug(f"pdftoppt warning threshold: {pdftoppt_warning_threshold}")

        enable_aspose = os.environ.get("PDF_TOOLS_ENABLE_ASPOSE", "0") == "1"
        method_sequence = []

        if enable_pdftoppt and HAS_PDFTOPPT:
            method_sequence.append(
                (
                    "pdftoppt",
                    lambda in_path, out_path: convert_with_pdftoppt(
                        in_path,
                        out_path,
                        warning_threshold=pdftoppt_warning_threshold,
                    ),
                )
            )
            method_sequence.append(("libreoffice", convert_with_libreoffice))
        else:
            method_sequence.append(("libreoffice", convert_with_libreoffice))

        if enable_pdftoppt and not HAS_PDFTOPPT:
            pdftoppt_unavailable = True
            method_errors["pdftoppt"] = "pdftoppt is enabled, but the package is not installed."
            log_debug("Experimental pdftoppt was enabled but package is not installed.")

        if enable_aspose and HAS_ASPOSE:
            method_sequence.append(("aspose", convert_with_aspose))
        elif enable_aspose and not HAS_ASPOSE:
            method_errors["aspose"] = "Aspose is enabled by environment, but the package is not installed."

        method_sequence.append(("custom_engine", convert_with_custom_engine))

        method_sequence.append(("image", convert_with_images))

        pending_methods = list(method_sequence)
        libreoffice_unavailable = False
        blank_output_detected = False
        visual_fallback_prioritized = False
        while pending_methods:
            method_name, method_func = pending_methods.pop(0)
            log_debug(f"Attempting {method_name} conversion...")
            success, message = _run_conversion_method(
                method_name,
                method_func,
                working_input_path,
                output_path,
                require_meaningful_content=source_has_visible_content,
            )
            log_debug(f"{method_name} result: {success}, {message}")

            if success:
                audit_logger.log_event("pdf_to_pptx", {
                    "input": input_path,
                    "output": output_path,
                    "method": method_name,
                })

                final_message = _finalize_success_message(message, effective_has_text, method_name)
                if ocr_note and ocr_temp_path:
                    final_message = f"{final_message} {ocr_note}"
                if libreoffice_unavailable and method_name != "libreoffice":
                    final_message = (
                        final_message
                        + " LibreOffice is still unavailable, so a fallback engine was used for this run."
                    )
                if blank_output_detected:
                    final_message = (
                        final_message
                        + " One or more earlier engines produced blank slides and were automatically skipped."
                    )
                if visual_fallback_prioritized and method_name == "image":
                    final_message = (
                        final_message
                        + " Visual fallback was prioritized because LibreOffice could not reliably export this PDF."
                    )
                if method_name == "pdftoppt":
                    final_message = (
                        final_message
                        + " Experimental pdftoppt engine was enabled for this run."
                    )
                if pdftoppt_warning_skipped and method_name != "pdftoppt":
                    final_message = (
                        final_message
                        + " pdftoppt was skipped because warning count exceeded the configured threshold."
                    )
                if pdftoppt_unavailable and method_name != "pdftoppt":
                    final_message = (
                        final_message
                        + " Experimental pdftoppt was enabled, but package availability was not detected in this Python environment."
                    )
                if pdftoppt_attempted and method_name != "pdftoppt":
                    final_message = (
                        final_message
                        + " Experimental pdftoppt was attempted first and then fell back to another engine."
                    )
                    if pdftoppt_failure_message:
                        final_message = (
                            final_message
                            + f" pdftoppt detail: {pdftoppt_failure_message}"
                        )
                return True, final_message

            method_errors[method_name] = message
            if method_name == "pdftoppt":
                pdftoppt_attempted = True
                pdftoppt_failure_message = message
            if method_name == "libreoffice" and "not found" in message.lower():
                libreoffice_unavailable = True
            if method_name == "libreoffice" and _should_prioritize_visual_fallback(message):
                visual_fallback_prioritized = True
                pending_methods.sort(key=lambda item: 0 if item[0] == "image" else 1)
            if method_name == "pdftoppt" and "warning threshold exceeded" in message.lower():
                pdftoppt_warning_skipped = True
            if "appears blank" in message.lower():
                blank_output_detected = True

        if method_errors:
            summary = "; ".join([f"{name}: {err}" for name, err in method_errors.items()])
            return False, f"All conversion methods failed. {summary}"

        return False, "No conversion methods were available."
        
    except Exception as e:
        log_debug(f"Exception during conversion: {str(e)}")
        return False, str(e)
    finally:
        _remove_file_safely(ocr_temp_path)
