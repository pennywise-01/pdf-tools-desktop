from pikepdf import Pdf

def remove_pages(input_path, output_path, page_numbers_str):
    """
    Removes specified pages from a PDF file.

    Args:
        input_path (str): The path to the input PDF file.
        output_path (str): The path to save the modified PDF file.
        page_numbers_str (str): A comma-separated string of page numbers to remove.
    """
    # Parse the page numbers string
    page_numbers = [int(p.strip()) for p in page_numbers_str.split(',') if p.strip()]

    with Pdf.open(input_path) as pdf:
        total_pages = len(pdf.pages)
        
        # Validate page numbers
        for page_num in page_numbers:
            if page_num < 1 or page_num > total_pages:
                raise ValueError(f"Invalid page number: {page_num}")

        # Create a new PDF without the specified pages
        new_pdf = Pdf.new()
        for i, page in enumerate(pdf.pages):
            if i + 1 not in page_numbers:
                new_pdf.pages.append(page)
        
        new_pdf.save(output_path)
