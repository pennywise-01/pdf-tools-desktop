import fitz
import os
from utils.audit_log import audit_logger

def extract_text_from_pdf(input_path, output_path):
    """
    Extracts all text from a PDF into a plain text file.
    """
    try:
        doc = fitz.open(input_path)
        text = ""
        for page in doc:
            text += page.get_text() + "\f" # Form feed character as page separator
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
            
        audit_logger.log_event("extract_text", {"input": input_path, "output": output_path})
        return True, "Text extracted successfully."
    except Exception as e:
        return False, str(e)
