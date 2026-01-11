import fitz
import os

def compress_pdf(input_path, output_path, quality=2):
    """
    Compresses a PDF file.
    
    Args:
        input_path (str): Path to input PDF.
        output_path (str): Path to save compressed PDF.
        quality (int): Compression level.
                       0 = None
                       1 = Clean (remove unused objects)
                       2 = Deflate (compress streams)
                       3 = Garbage 3 (deduplicate)
                       4 = Maximum (deduplicate + distinct)
    """
    try:
        doc = fitz.open(input_path)
        
        # Map quality slider (0-100) or int to garbage collection levels
        # Assuming input 0-4 for simplicity in API, UI can map slider
        garbage_level = quality
        
        if garbage_level < 0: garbage_level = 0
        if garbage_level > 4: garbage_level = 4
        
        # Additional options
        deflate = True if garbage_level >= 2 else False
        clean = True if garbage_level >= 1 else False
        
        doc.save(
            output_path,
            garbage=garbage_level,
            deflate=deflate,
            clean=clean
        )
        doc.close()
    except Exception as e:
        raise IOError(f"Failed to compress PDF: {e}")
