from pikepdf import Pdf

def rotate_pages(input_path, output_path, page_number, angle):
    """
    Rotates a page in a PDF file.

    Args:
        input_path (str): The path to the input PDF file.
        output_path (str): The path to save the modified PDF file.
        page_number (int): The number of the page to rotate (1-based).
        angle (int): The rotation angle (must be a multiple of 90).
    """
    if angle % 90 != 0:
        raise ValueError("Rotation angle must be a multiple of 90.")

    with Pdf.open(input_path) as pdf:
        if page_number < 1 or page_number > len(pdf.pages):
            raise ValueError(f"Invalid page number: {page_number}")
        
        pdf.pages[page_number - 1].rotate(angle, relative=True)
        pdf.save(output_path)
