from pdf2docx import Converter
from utils.audit_log import audit_logger
import os

def convert_pdf_to_word(input_path, output_path):
    """
    Convert a PDF into a Microsoft Word (`.docx`) file.
    """
    try:
        # pdf2docx is verbose, might want to suppress output or handle logging.
        # But for now, simple usage.
        cv = Converter(input_path)
        cv.convert(output_path, start=0, end=None)
        cv.close()
        
        audit_logger.log_event("pdf_to_word", {"input": input_path, "output": output_path})
        return True, "Converted to Word successfully."
    except Exception as e:
        return False, str(e)
