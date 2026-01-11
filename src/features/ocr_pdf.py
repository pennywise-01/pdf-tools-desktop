import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import os
import sys

# Attempt to locate Tesseract executable if not in PATH
def setup_tesseract():
    """
    Checks for Tesseract availability. 
    Returns True if found (or configured), False otherwise.
    """
    # 1. Check if already configured and valid
    if hasattr(pytesseract.pytesseract, 'tesseract_cmd') and \
       os.path.exists(pytesseract.pytesseract.tesseract_cmd) and \
       pytesseract.pytesseract.tesseract_cmd != 'tesseract':
        return True

    # 2. Check environment variable
    if 'TESSERACT_CMD' in os.environ and os.path.exists(os.environ['TESSERACT_CMD']):
        pytesseract.pytesseract.tesseract_cmd = os.environ['TESSERACT_CMD']
        return True
        
    # 3. Check common Windows paths
    if sys.platform.startswith('win'):
        possible_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.join(os.getenv('LOCALAPPDATA', ''), r"Tesseract-OCR\tesseract.exe"),
        ]
        for path in possible_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                return True
                
    # 4. Check system PATH (by trying to execute it, or just trusting shutil.which if we used it)
    # pytesseract defaults to 'tesseract', which relies on PATH. 
    # We can assume if we didn't find it explicitly, and it's not in PATH, it's missing.
    try:
        # pytesseract.get_tesseract_version() raises TesseractNotFoundError if missing
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False

# Run setup initially
setup_tesseract()

def ocr_pdf(input_path, output_path, language='eng', progress_callback=None):
    """
    Applies OCR to a PDF using Tesseract, creating a searchable PDF.
    
    Args:
        input_path (str): Path to source PDF.
        output_path (str): Path to save OCR'd PDF.
        language (str): Language code (e.g., 'eng').
        progress_callback (func): Function accepting an integer (0-100).
    """
    try:
        doc = fitz.open(input_path)
        result_pdf = fitz.open()
        
        total_pages = len(doc)
        
        for i in range(total_pages):
            if progress_callback:
                progress_callback(int((i / total_pages) * 100))
                
            page = doc.load_page(i)
            # High dpi render for better OCR
            # 300 DPI is standard for OCR.
            pix = page.get_pixmap(dpi=300)
            
            # Safety check for extremely large images to prevent OOM
            if pix.width * pix.height > 100_000_000: # > 100 Megapixels
                # Downscale if too big
                print(f"Page {i+1} is too large for 300 DPI OCR. Downscaling...")
                pix = page.get_pixmap(dpi=150)
            
            img_data = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_data))
            
            # Get PDF data from Tesseract
            # This returns a full PDF page with image + text layer
            pdf_bytes = pytesseract.image_to_pdf_or_hocr(image, extension='pdf', lang=language)
            
            ocr_page_doc = fitz.open("pdf", pdf_bytes)
            result_pdf.insert_pdf(ocr_page_doc)
            
        result_pdf.save(output_path)
        doc.close()
        result_pdf.close()
        return True
        
    except pytesseract.TesseractNotFoundError:
        raise RuntimeError("Tesseract OCR is not found. Please install Tesseract-OCR.")
    except Exception as e:
        raise RuntimeError(f"OCR failed: {e}")
