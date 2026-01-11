import fitz
import os
import sys
import subprocess
import tempfile
import shutil
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


def find_libreoffice():
    """Find LibreOffice installation path."""
    possible_paths = [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        shutil.which("soffice"),
        shutil.which("libreoffice"),
    ]
    for path in possible_paths:
        if path and os.path.exists(path):
            return path
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
    Convert PDF to PPTX using LibreOffice.
    LibreOffice can import PDF and export to various formats with good formatting preservation.
    """
    soffice = find_libreoffice()
    if not soffice:
        return False, "LibreOffice not found"
    
    try:
        # Create temp directory for output
        temp_dir = tempfile.mkdtemp()
        
        # LibreOffice command to convert PDF to PPTX
        # --headless: no GUI
        # --convert-to: output format
        # --outdir: output directory
        cmd = [
            soffice,
            "--headless",
            "--infilter=impress_pdf_import",
            "--convert-to", "pptx",
            "--outdir", temp_dir,
            input_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        # Find the converted file
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        temp_output = os.path.join(temp_dir, f"{base_name}.pptx")
        
        if os.path.exists(temp_output):
            shutil.move(temp_output, output_path)
            shutil.rmtree(temp_dir, ignore_errors=True)
            return True, "Converted with LibreOffice (editable text preserved)"
        else:
            shutil.rmtree(temp_dir, ignore_errors=True)
            return False, f"LibreOffice conversion failed: {result.stderr}"
            
    except subprocess.TimeoutExpired:
        return False, "LibreOffice conversion timed out"
    except Exception as e:
        return False, str(e)


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



def convert_pdf_to_pptx(input_path, output_path):
    """
    Convert PDF to PowerPoint (PPTX).
    
    Strategy:
    1. Try Enhanced Custom Engine (Python-based, editable text & layout, no external deps)
    2. Try Aspose (Legacy Support)
    3. Try LibreOffice
    4. Fallback to Images
    """
    try:
        # 1. Try Custom Engine first (Robust, format preserving, no crashes)
        success, message = convert_with_custom_engine(input_path, output_path)
        if success:
            audit_logger.log_event("pdf_to_pptx", {
                "input": input_path, 
                "output": output_path,
                "method": "custom_engine"
            })
            return True, message

        aspose_error = None
        # Try Aspose second
        # if HAS_ASPOSE:
        #     success, message = convert_with_aspose(input_path, output_path)
        #     if success:
        #         audit_logger.log_event("pdf_to_pptx", {
        #             "input": input_path, 
        #             "output": output_path,
        #             "method": "aspose"
        #         })
        #         return True, message
        #     else:
        #         aspose_error = message
        
        # Try LibreOffice third
        # success, message = convert_with_libreoffice(input_path, output_path)
        # if success:
        #     audit_logger.log_event("pdf_to_pptx", {
        #         "input": input_path, 
        #         "output": output_path,
        #         "method": "libreoffice"
        #     })
        #     return True, message
        
        # Fall back to image-based conversion
        # success, message = convert_with_images(input_path, output_path)
        # if success:
        #     audit_logger.log_event("pdf_to_pptx", {
        #         "input": input_path, 
        #         "output": output_path,
        #         "method": "image"
        #     })
        #     hint = ""
        #     if not HAS_ASPOSE:
        #         hint = " (pip install aspose.slides for editable text)"
        #     return True, message + hint
        
        # if aspose_error:
        #    return False, f"Aspose conversion failed: {aspose_error}. Fallback methods also failed."
            
        return False, "Custom conversion engine failed."
        
    except Exception as e:
        return False, str(e)
