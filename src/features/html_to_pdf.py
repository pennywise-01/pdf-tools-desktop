import pdfkit
import shutil
import os
import sys
import subprocess
import webbrowser

def get_wkhtmltopdf_config():
    """
    Locate wkhtmltopdf executable and return pdfkit configuration.
    Checks:
    1. Local 'bin' folder (for self-contained app)
    2. System PATH
    3. Common Windows install locations
    """
    # 1. Check local bin folder (relative to project root)
    # Assuming src/features/html_to_pdf.py -> ../../bin
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    local_bin = os.path.join(base_dir, "bin", "wkhtmltopdf", "bin", "wkhtmltopdf.exe")
    
    if os.path.exists(local_bin):
        return pdfkit.configuration(wkhtmltopdf=local_bin)

    # 2. Check System PATH
    if shutil.which("wkhtmltopdf"):
        return None # Default configuration uses PATH

    # 3. Check common Windows locations
    common_paths = [
        r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe",
        r"C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe"
    ]
    for path in common_paths:
        if os.path.exists(path):
            return pdfkit.configuration(wkhtmltopdf=path)
            
    return None

def is_wkhtmltopdf_installed():
    return get_wkhtmltopdf_config() is not None or shutil.which("wkhtmltopdf") is not None

def install_wkhtmltopdf_help():
    """
    Attempts to help the user install wkhtmltopdf.
    Returns True if installation was attempted (user might need to restart app),
    False if user cancelled or failed.
    """
    # Check for winget
    if shutil.which("winget"):
        try:
            # We can't easily run interactive winget from here without a console,
            # but we can try to launch it in a new visible console window.
            # Or just open the download page which is safer.
            pass
        except Exception:
            pass
            
    # Fallback: Open browser
    webbrowser.open("https://wkhtmltopdf.org/downloads.html")
    return True

def convert_html_to_pdf(source, output_path):
    config = get_wkhtmltopdf_config()
    
    # If config is None (not found in local or common paths), 
    # pdfkit will try PATH. If that fails, we raise error.
    if config is None and not shutil.which("wkhtmltopdf"):
        raise RuntimeError(
            "wkhtmltopdf is not installed. \n"
            "Please install it to use this feature."
        )

    is_url = source.startswith("http://") or source.startswith("https://")
    
    # Options to make wkhtmltopdf more robust
    options = {
        'enable-local-file-access': None,
        'load-error-handling': 'ignore',
        'no-stop-slow-scripts': None
    }

    try:
        if is_url:
            pdfkit.from_url(source, output_path, configuration=config, options=options)
        else:
            if not os.path.exists(source):
                raise FileNotFoundError(f"Input file not found: {source}")
            pdfkit.from_file(source, output_path, configuration=config, options=options)
    except Exception as e:
        raise IOError(f"Failed to convert HTML to PDF: {e}")
