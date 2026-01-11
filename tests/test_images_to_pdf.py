import os
import pytest
from PIL import Image
from src.features.images_to_pdf import convert_images_to_pdf

@pytest.fixture
def create_dummy_images(tmp_path):
    image_paths = []
    for i in range(2):
        image_path = tmp_path / f"test_image_{i}.png"
        img = Image.new('RGB', (100, 100), color = 'red')
        img.save(image_path)
        image_paths.append(str(image_path))
    return image_paths

def test_convert_images_to_pdf(create_dummy_images, tmp_path):
    output_path = tmp_path / "output.pdf"
    convert_images_to_pdf(create_dummy_images, str(output_path))
    assert os.path.exists(output_path)
