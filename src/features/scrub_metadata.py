from pikepdf import Pdf

def scrub_metadata(input_path, output_path):
    """
    Removes all metadata from a PDF file.

    Args:
        input_path (str): The path to the input PDF file.
        output_path (str): The path to save the scrubbed PDF file.
    """
    with Pdf.open(input_path) as pdf:
        # The docinfo dictionary contains the metadata.
        # We can't delete it directly, but we can clear it.
        # Saving the PDF without metadata is achieved by creating a new PDF
        # and copying the pages.
        new_pdf = Pdf.new()
        new_pdf.pages.extend(pdf.pages)
        new_pdf.save(output_path)
