import fitz
import os

def convert_pdf_to_images(pdf_path, output_dir, format="png", dpi=300):
    """
    Converts pages of a PDF file to images.
    
    Args:
        pdf_path (str): Path to the input PDF file.
        output_dir (str): Directory to save the images.
        format (str): Image format (png, jpg).
        dpi (int): Resolution in DPI.
    
    Returns:
        list: List of paths to the generated images.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    doc = fitz.open(pdf_path)
    output_files = []
    
    # Calculate zoom factor based on DPI (default PDF is 72 DPI)
    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)
    
    for i, page in enumerate(doc):
        pix = page.get_pixmap(matrix=mat)
        output_filename = f"page_{i+1}.{format}"
        output_path = os.path.join(output_dir, output_filename)
        
        pix.save(output_path)
        output_files.append(output_path)
        
    doc.close()
    return output_files
