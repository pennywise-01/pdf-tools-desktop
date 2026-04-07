import os
import sys
import subprocess
import shutil
import tempfile
import logging
import time

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
        
        candidates = []

        env_override = os.environ.get("PDF_TOOLS_SOFFICE_PATH")
        if env_override:
            candidates.append(env_override)

        candidates.extend([
            os.path.join(project_root, "LibreOfficePortable", "App", "libreoffice", "program", "soffice.exe"),
            os.path.join(project_root, "LibreOfficePortable", "LibreOfficePortable", "App", "libreoffice", "program", "soffice.exe"),
        ])

        try:
            for entry in os.listdir(project_root):
                entry_path = os.path.join(project_root, entry)
                if not os.path.isdir(entry_path):
                    continue

                if "libreofficeportable" not in entry.lower():
                    continue

                candidates.extend([
                    os.path.join(entry_path, "App", "libreoffice", "program", "soffice.exe"),
                    os.path.join(entry_path, "LibreOfficePortable", "App", "libreoffice", "program", "soffice.exe"),
                ])
        except Exception:
            pass

        candidates.extend([
            r"C:\LibreOffice\program\soffice.exe",
            r"C:\LibreOfficePortable\App\libreoffice\program\soffice.exe",
            r"C:\PortableApps\LibreOfficePortable\App\libreoffice\program\soffice.exe",
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
            shutil.which("soffice"),
            shutil.which("libreoffice"),
        ])

        seen = set()
        for soffice_path in candidates:
            if not soffice_path:
                continue

            normalized = os.path.normpath(soffice_path)
            if normalized in seen:
                continue
            seen.add(normalized)

            if os.path.exists(normalized):
                return os.path.abspath(normalized)
        
        return None

    def _emit_debug(self, debug_logger, level, message):
        if level == "warning":
            logging.warning(message)
        else:
            logging.info(message)

        if debug_logger:
            try:
                debug_logger(message)
            except Exception:
                pass

    def convert_to_pptx(self, input_pdf_path, output_dir=None, timeout=300, debug_logger=None):
        """
        Converts a PDF file to PPTX using LibreOffice in headless mode.

        Returns:
            str: Absolute path to the converted PPTX file.
        """
        if not os.path.exists(input_pdf_path):
            raise FileNotFoundError(f"Input file not found: {input_pdf_path}")
            
        if output_dir is None:
            output_dir = os.path.dirname(input_pdf_path)
            
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Use a dedicated temporary profile to avoid conflicts with existing LibreOffice instances.
        # Cleanup is best-effort because LibreOffice may keep short-lived locks on updater logs.
        temp_user_dir = tempfile.mkdtemp(prefix="pdf_tools_lo_profile_")
        try:
            user_installation_url = f"file:///{temp_user_dir.replace(os.sep, '/')}"

            base_name = os.path.splitext(os.path.basename(input_pdf_path))[0]
            expected_output = os.path.join(output_dir, f"{base_name}.pptx")

            attempts = [
                [
                    self.soffice_path,
                    "--headless",
                    "--nologo",
                    "--nodefault",
                    "--norestore",
                    "--infilter=impress_pdf_import",
                    "--convert-to", 'pptx:"Impress MS PowerPoint 2007 XML"',
                    f"-env:UserInstallation={user_installation_url}",
                    "--outdir", output_dir,
                    input_pdf_path,
                ],
                [
                    self.soffice_path,
                    "--headless",
                    "--nologo",
                    "--nodefault",
                    "--norestore",
                    "--convert-to", 'pptx:"Impress MS PowerPoint 2007 XML"',
                    f"-env:UserInstallation={user_installation_url}",
                    "--outdir", output_dir,
                    input_pdf_path,
                ],
                [
                    self.soffice_path,
                    "--headless",
                    "--nologo",
                    "--nodefault",
                    "--norestore",
                    "--convert-to", "pptx",
                    f"-env:UserInstallation={user_installation_url}",
                    "--outdir", output_dir,
                    input_pdf_path,
                ],
            ]

            # startupinfo to hide the console window on Windows
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            last_error = None
            for attempt_index, cmd in enumerate(attempts, start=1):
                start_time = time.time()
                self._emit_debug(
                    debug_logger,
                    "info",
                    f"LibreOffice attempt {attempt_index}/{len(attempts)} command: {' '.join(cmd)}",
                )

                try:
                    result = subprocess.run(
                        cmd,
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        startupinfo=startupinfo,
                        timeout=timeout,
                    )
                except subprocess.CalledProcessError as e:
                    last_error = RuntimeError(f"Conversion failed: {e.stderr}")
                    self._emit_debug(
                        debug_logger,
                        "warning",
                        f"LibreOffice attempt {attempt_index} failed: {(e.stderr or '').strip()}",
                    )
                    continue
                except subprocess.TimeoutExpired:
                    last_error = RuntimeError("Conversion timed out.")
                    self._emit_debug(
                        debug_logger,
                        "warning",
                        f"LibreOffice attempt {attempt_index} timed out.",
                    )
                    continue

                generated = self._find_generated_pptx(output_dir, expected_output, start_time)
                if generated:
                    self._emit_debug(
                        debug_logger,
                        "info",
                        f"LibreOffice conversion successful on attempt {attempt_index}: {generated}",
                    )
                    return os.path.abspath(generated)

                # Some LibreOffice builds log output path to stdout even when delayed on disk writes.
                generated_from_stdout = self._extract_pptx_path_from_stdout(result.stdout)
                if generated_from_stdout and os.path.exists(generated_from_stdout):
                    self._emit_debug(
                        debug_logger,
                        "info",
                        f"LibreOffice conversion successful on attempt {attempt_index} (stdout path): {generated_from_stdout}",
                    )
                    return os.path.abspath(generated_from_stdout)

                last_error = RuntimeError("LibreOffice did not produce an output PPTX file.")
                self._emit_debug(
                    debug_logger,
                    "warning",
                    (
                        f"LibreOffice attempt {attempt_index} produced no discoverable PPTX output. "
                        f"stdout={(result.stdout or '').strip()} stderr={(result.stderr or '').strip()}"
                    ),
                )

            if last_error:
                self._emit_debug(debug_logger, "warning", f"LibreOffice final error: {last_error}")
                raise last_error

            raise RuntimeError("LibreOffice conversion failed for an unknown reason.")
        finally:
            try:
                shutil.rmtree(temp_user_dir, ignore_errors=True)
            except Exception:
                # Ignore cleanup failures to avoid masking successful conversion output.
                pass

    def _find_generated_pptx(self, output_dir, expected_output, min_mtime):
        """Return generated PPTX path if discovered."""
        if os.path.exists(expected_output):
            return expected_output

        candidates = []
        try:
            for name in os.listdir(output_dir):
                if not name.lower().endswith(".pptx"):
                    continue
                full_path = os.path.join(output_dir, name)
                try:
                    mtime = os.path.getmtime(full_path)
                except OSError:
                    continue

                if mtime >= (min_mtime - 1.0):
                    candidates.append((mtime, full_path))
        except Exception:
            return None

        if not candidates:
            return None

        candidates.sort(key=lambda item: item[0], reverse=True)
        return candidates[0][1]

    def _extract_pptx_path_from_stdout(self, stdout_text):
        """Try to parse generated output path from LibreOffice stdout text."""
        if not stdout_text:
            return None

        for line in stdout_text.splitlines():
            marker = "->"
            if marker not in line:
                continue

            right = line.split(marker, 1)[1].strip()
            if " using filter" in right:
                right = right.split(" using filter", 1)[0].strip()

            if right.lower().endswith(".pptx"):
                return os.path.normpath(right)

        return None

