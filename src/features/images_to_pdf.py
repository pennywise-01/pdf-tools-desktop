from PIL import Image
import fitz  # PyMuPDF
import io

def convert_images_to_pdf(image_paths, output_path):
    if not image_paths:
        raise ValueError("No image paths provided")

    doc = fitz.open()

    for image_path in image_paths:
        try:
            with Image.open(image_path) as img:
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG')
                img_byte_arr = img_byte_arr.getvalue()
                
                img_xref = doc.new_page(width=img.width, height=img.height)
                img_xref.insert_image(img_xref.rect, stream=img_byte_arr)
        except Exception as e:
            raise IOError(f"Failed to process image {image_path}: {e}")

    doc.save(output_path)
    doc.close()
