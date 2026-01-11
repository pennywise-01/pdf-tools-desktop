from pikepdf import Pdf

def split_pdf(input_path, output_path, page_range):
    """
    Splits a PDF file based on a page range string.

    Args:
        input_path (str): The path to the input PDF file.
        output_path (str): The path to save the split PDF file.
        page_range (str): A string representing the page range (e.g., "1-5, 8, 11-15").
    """
    with Pdf.open(input_path) as pdf:
        total_pages = len(pdf.pages)
        selected_pages = set()
        
        # Parse the page range string
        ranges = page_range.split(',')
        for r in ranges:
            r = r.strip()
            if '-' in r:
                start, end = r.split('-')
                start = int(start)
                end = int(end)
                if start > end or start < 1 or end > total_pages:
                    raise ValueError(f"Invalid page range: {r}")
                for i in range(start, end + 1):
                    selected_pages.add(i)
            else:
                page_num = int(r)
                if page_num < 1 or page_num > total_pages:
                    raise ValueError(f"Invalid page number: {page_num}")
                selected_pages.add(page_num)

        # Create a new PDF with the selected pages
        new_pdf = Pdf.new()
        for i in sorted(list(selected_pages)):
            new_pdf.pages.append(pdf.pages[i-1])
        
        new_pdf.save(output_path)
