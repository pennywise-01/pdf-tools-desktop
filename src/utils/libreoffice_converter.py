import os
import sys
import subprocess
import shutil
import tempfile
import logging

class LibreOfficeConverter:
    def __init__(self):
        self.soffice_path = self._find_soffice()
        if not self.soffice_path:
            raise FileNotFoundError("LibreOffice executable (soffice.exe) not found.")

    def _find_soffice(self):
        """
        Dynamically locate soffice.exe.
        Assumes it is located in LibreOfficePortable/App/libreoffice/program/soffice.exe
        relative to the project root.
        """
        # Get the absolute path of the current file (src/utils/libreoffice_converter.py)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Navigate up to the project root (src/utils -> src -> root)
        project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
        
        candidates = [
            os.path.join(project_root, "LibreOfficePortable", "App", "libreoffice", "program", "soffice.exe"),
            os.path.join(project_root, "LibreOfficePortable", "LibreOfficePortable", "App", "libreoffice", "program", "soffice.exe"),
            r"C:\LibreOffice\program\soffice.exe",
            r"C:\LibreOfficePortable\App\libreoffice\program\soffice.exe",
            r"C:\PortableApps\LibreOfficePortable\App\libreoffice\program\soffice.exe",
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
            shutil.which("soffice"),
            shutil.which("libreoffice"),
        ]

        for soffice_path in candidates:
            if soffice_path and os.path.exists(soffice_path):
                return soffice_path
        
        return None

    def convert_to_pptx(self, input_pdf_path, output_dir=None):
        """
        Converts a PDF file to PPTX using LibreOffice in headless mode.
        """
        if not os.path.exists(input_pdf_path):
            raise FileNotFoundError(f"Input file not found: {input_pdf_path}")
            
        if output_dir is None:
            output_dir = os.path.dirname(input_pdf_path)
            
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Create a temporary directory for the UserInstallation profile
        # This prevents conflicts with running instances of LibreOffice
        with tempfile.TemporaryDirectory() as temp_user_dir:
            # Convert temp_user_dir to URL format for LibreOffice
            # Windows paths need to be properly formatted for the -env flag
            user_installation_url = f"file:///{temp_user_dir.replace(os.sep, '/')}"
            
            cmd = [
                self.soffice_path,
                "--headless",
                "--infilter=impress_pdf_import",
                "--convert-to", 'pptx:"Impress MS PowerPoint 2007 XML"',
                f"-env:UserInstallation={user_installation_url}",
                "--outdir", output_dir,
                input_pdf_path
            ]
            
            logging.info(f"Running LibreOffice conversion: {' '.join(cmd)}")
            
            try:
                # Run the command
                # startupinfo to hide the console window on Windows
                startupinfo = None
                if os.name == 'nt':
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
                result = subprocess.run(
                    cmd, 
                    check=True, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    text=True,
                    startupinfo=startupinfo
                )
                
                logging.info("Conversion successful.")
                return True
                
            except subprocess.CalledProcessError as e:
                logging.error(f"LibreOffice conversion failed: {e.stderr}")
                raise RuntimeError(f"Conversion failed: {e.stderr}")

