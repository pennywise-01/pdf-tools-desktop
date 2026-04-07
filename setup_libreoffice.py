import os
import sys
import shutil
import urllib.request
import subprocess

# Configuration
DOWNLOAD_URL = "https://portableapps.com/redir2/?a=LibreOfficePortable&s=s&p=https://download.documentfoundation.org/libreoffice/portable/25.2.3/&d=pb&f=LibreOfficePortable_25.2.3_MultilingualStandard.paf.exe"
INSTALLER_FILENAME = "LibreOfficePortable_Installer.exe"
INSTALL_DIR_NAME = "LibreOfficePortable"

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    installer_path = os.path.join(base_dir, INSTALLER_FILENAME)
    install_dir = os.path.join(base_dir, INSTALL_DIR_NAME)
    malformed_install_dir = os.path.join(base_dir, f"{INSTALL_DIR_NAME}{INSTALL_DIR_NAME}")

    print(f"Working directory: {base_dir}")

    # 1. Download
    if not os.path.exists(installer_path):
        print(f"Downloading LibreOffice Portable from {DOWNLOAD_URL}...")
        try:
            # Add User-Agent headers to avoid being blocked
            req = urllib.request.Request(
                DOWNLOAD_URL, 
                data=None, 
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
            )
            with urllib.request.urlopen(req) as response, open(installer_path, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
            print("Download complete.")
        except Exception as e:
            print(f"Failed to download: {e}")
            sys.exit(1)
    else:
        print("Installer already exists.")

    # 2. Extract
    existing_install_dir = None
    for candidate in [install_dir, malformed_install_dir]:
        if os.path.exists(os.path.join(candidate, "App", "libreoffice", "program", "soffice.exe")):
            existing_install_dir = candidate
            break

    if existing_install_dir is None:
        print(f"Extracting to {base_dir}...")
        # Use subprocess to run the .paf.exe
        # Arguments: /DESTINATION=<path> /VERYSILENT /SUPPRESSMSGBOXES
        # Note: /DESTINATION requires absolute path
        cmd = [installer_path, f"/DESTINATION={base_dir}", "/VERYSILENT", "/SUPPRESSMSGBOXES"]
        try:
            print(f"Running command: {' '.join(cmd)}")
            subprocess.check_call(cmd)
            print("Extraction complete.")
        except Exception as e:
            print(f"Extraction failed: {e}")
            print("Please ensure you are running this on Windows and have permission to execute the installer.")
            sys.exit(1)

        for candidate in [install_dir, malformed_install_dir]:
            if os.path.exists(os.path.join(candidate, "App", "libreoffice", "program", "soffice.exe")):
                existing_install_dir = candidate
                break
    else:
        print(f"Directory {existing_install_dir} already exists. Skipping extraction.")

    # 3. Optimize
    print("Running Lite Optimization...")
    # Standard PortableApps structure: App/libreoffice/
    install_root = existing_install_dir if existing_install_dir else install_dir
    app_dir = os.path.join(install_root, "App", "libreoffice")
    
    if not os.path.exists(app_dir):
        print(f"Warning: {app_dir} not found. Structure might be different or extraction failed.")
        return

    # Delete folders
    to_delete = [
        os.path.join(app_dir, "help"),
        os.path.join(app_dir, "share", "gallery"),
    ]
    
    for path in to_delete:
        if os.path.exists(path):
            print(f"Deleting {path}...")
            try:
                shutil.rmtree(path)
            except Exception as e:
                print(f"Warning: Could not delete {path}: {e}")

    # Clean dicts
    dict_dir = os.path.join(app_dir, "share", "dict")
    if os.path.exists(dict_dir):
        print(f"Cleaning dictionaries in {dict_dir}...")
        for name in os.listdir(dict_dir):
            # Keep en-US and related files.
            if "en-US" in name or "en_US" in name:
                continue
            
            file_path = os.path.join(dict_dir, name)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"Error removing {name}: {e}")
    
    # 4. Verify
    soffice = os.path.join(app_dir, "program", "soffice.exe")
    if os.path.exists(soffice):
        print(f"Success! soffice.exe found at {soffice}")
        print("You can now use LibreOffice Portable.")
    else:
        print(f"Warning: soffice.exe not found at {soffice}")

if __name__ == "__main__":
    main()
