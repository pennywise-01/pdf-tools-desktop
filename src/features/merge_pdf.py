from pikepdf import Pdf

def merge_pdfs(pdf_files, output_path):
    """
    Merges a list of PDF files into a single PDF file.

    Args:
        pdf_files (list): A list of paths to the PDF files to merge.
        output_path (str): The path to save the merged PDF file.
    """
    pdf = Pdf.new()
    for file in pdf_files:
        with Pdf.open(file) as src:
            pdf.pages.extend(src.pages)
    pdf.save(output_path)
