import os
import sys
import subprocess
import urllib.request
import tempfile

TESSERACT_INSTALLER_URL = "https://github.com/UB-Mannheim/tesseract/releases/download/v5.4.0.20240606/tesseract-ocr-w64-setup-5.4.0.20240606.exe"

def download_installer(progress_callback=None):
    """
    Downloads the Tesseract installer to a temporary file.
    
    Args:
        progress_callback (func): Function accepting int (0-100).
        
    Returns:
        str: Path to the downloaded installer.
    """
    temp_dir = tempfile.gettempdir()
    installer_path = os.path.join(temp_dir, "tesseract_installer.exe")
    
    try:
        # Create request with User-Agent to avoid blocking
        req = urllib.request.Request(
            TESSERACT_INSTALLER_URL, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        )
        
        with urllib.request.urlopen(req) as response:
            total_size = int(response.info().get('Content-Length').strip())
            downloaded = 0
            block_size = 8192
            
            with open(installer_path, 'wb') as f:
                while True:
                    chunk = response.read(block_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback:
                        percent = int((downloaded / total_size) * 100)
                        progress_callback(percent)
                        
        return installer_path
    except Exception as e:
        if os.path.exists(installer_path):
            os.remove(installer_path)
        raise e

def run_installer(installer_path):
    """
    Runs the Tesseract installer with administrative privileges.
    
    Args:
        installer_path (str): Path to the installer executable.
        
    Returns:
        bool: True if installation completed, False otherwise.
    """
    try:
        print(f"Running installer: {installer_path}")
        
        # Use PowerShell to run with elevation (RunAs) and wait for completion.
        # This fixes [WinError 740] The requested operation requires elevation.
        cmd = [
            "powershell",
            "-Command",
            f"Start-Process -FilePath '{installer_path}' -Verb RunAs -Wait"
        ]
        
        # Check=True will raise CalledProcessError if user cancels UAC or if PS fails
        subprocess.run(cmd, check=True)
        return True
        
    except subprocess.CalledProcessError:
        print("Installer execution cancelled or failed (UAC denied?).")
        return False
    except Exception as e:
        print(f"Failed to run installer: {e}")
        return False
