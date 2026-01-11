import pikepdf
import fitz  # PyMuPDF
import os

def repair_pdf(input_path, output_path):
    """
    Repairs a corrupted PDF by rebuilding the XREF table.
    
    Args:
        input_path (str): Path to the corrupted PDF.
        output_path (str): Path to save the repaired PDF.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        # First try with pikepdf (it handles recovery well)
        try:
            pdf = pikepdf.Pdf.open(input_path, recover=True)
            pdf.save(output_path)
            return True
        except Exception as e:
            print(f"pikepdf repair failed: {e}")
            
            # Fallback to PyMuPDF (Clean & defrag)
            doc = fitz.open(input_path)
            # garbage=4 (clean unused objects), deflate=True (compress streams)
            doc.save(output_path, garbage=4, deflate=True)
            doc.close()
            return True
            
    except Exception as e:
        print(f"Repair failed: {e}")
        return False
