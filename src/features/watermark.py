import fitz

def add_watermark(input_path, output_path, text, opacity=0.3, rotation=45, font_size=50, color=(0, 0, 0)):
    """
    Adds a text watermark to all pages of a PDF.
    
    Args:
        input_path (str): Path to input PDF.
        output_path (str): Path to save watermarked PDF.
        text (str): Watermark text.
        opacity (float): Opacity of the watermark (0.0 to 1.0).
        rotation (int): Rotation angle in degrees.
        font_size (int): Font size.
        color (tuple): RGB color tuple (0-1 range).
    """
    try:
        doc = fitz.open(input_path)
        
        fontname = "helv"
        
        for page in doc:
            # Calculate text dimensions to center it
            text_len = fitz.get_text_length(text, fontname=fontname, fontsize=font_size)
            text_height = font_size
            
            # Center of page
            cx, cy = page.rect.width / 2, page.rect.height / 2
            
            # Rotation matrix
            mat = fitz.Matrix(rotation)
            
            # Calculate start point so text is centered
            # Text insertion point is bottom-left usually.
            # Center of text relative to insertion point (approximate)
            # y is 0 at baseline. center is slightly up? or down?
            # insert_text origin is baseline.
            p_center = fitz.Point(text_len / 2, -text_height * 0.3) 
            p_rotated = p_center * mat
            start_point = fitz.Point(cx, cy) - p_rotated
            
            morph = (start_point, mat)

            page.insert_text(
                start_point,
                text,
                fontsize=font_size,
                fontname=fontname,
                morph=morph,
                fill_opacity=opacity,
                color=color,
            )
            
        doc.save(output_path)
        doc.close()
    except Exception as e:
        raise IOError(f"Failed to add watermark: {e}")
