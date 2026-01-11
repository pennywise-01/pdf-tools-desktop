import os
import pytest
from unittest.mock import patch, MagicMock
from src.features.html_to_pdf import convert_html_to_pdf

@pytest.fixture
def html_file(tmp_path):
    p = tmp_path / "test.html"
    p.write_text("<html><body><h1>Hello World</h1></body></html>", encoding="utf-8")
    return str(p)

@patch("src.features.html_to_pdf.pdfkit")
@patch("src.features.html_to_pdf.shutil.which")
def test_convert_html_to_pdf_file(mock_which, mock_pdfkit, html_file, tmp_path):
    mock_which.return_value = "/usr/bin/wkhtmltopdf"  # Mock existence of binary
    output_path = tmp_path / "output.pdf"
    
    convert_html_to_pdf(html_file, str(output_path))
    
    # Verify call arguments, ignoring configuration object identity
    args, kwargs = mock_pdfkit.from_file.call_args
    assert args[0] == html_file
    assert args[1] == str(output_path)
    assert "options" in kwargs
    assert kwargs["options"]["enable-local-file-access"] is None

@patch("src.features.html_to_pdf.pdfkit")
@patch("src.features.html_to_pdf.shutil.which")
def test_convert_html_to_pdf_url(mock_which, mock_pdfkit, tmp_path):
    mock_which.return_value = "/usr/bin/wkhtmltopdf"
    url = "http://example.com"
    output_path = tmp_path / "output.pdf"
    
    convert_html_to_pdf(url, str(output_path))
    
    args, kwargs = mock_pdfkit.from_url.call_args
    assert args[0] == url
    assert args[1] == str(output_path)
    assert "options" in kwargs

@patch("src.features.html_to_pdf.os.path.exists")
@patch("src.features.html_to_pdf.shutil.which")
def test_convert_html_to_pdf_missing_binary(mock_which, mock_exists, html_file, tmp_path):
    mock_which.return_value = None
    
    # Mock exists to return True only for the input html file, False for wkhtmltopdf paths
    def side_effect(path):
        return str(path) == str(html_file)
    mock_exists.side_effect = side_effect
    
    output_path = tmp_path / "output.pdf"
    
    with pytest.raises(RuntimeError, match="wkhtmltopdf is not installed"):
        convert_html_to_pdf(html_file, str(output_path))
