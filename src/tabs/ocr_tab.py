from PyQt6.QtWidgets import (
    QPushButton, QLabel, QMessageBox, QFileDialog, QProgressDialog,
    QVBoxLayout, QComboBox
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont

from widgets.feature_tab import FeatureTab
from features.ocr_pdf import ocr_pdf, setup_tesseract
from utils.tesseract_installer import download_installer, run_installer
from network_security import temporarily_allow_network

class InstallTesseractWorker(QThread):
    progress_update = pyqtSignal(int)
    finished = pyqtSignal(bool, str) # success, message

    def run(self):
        try:
            self.progress_update.emit(0)
            
            # Temporarily unlock network for download
            with temporarily_allow_network():
                installer_path = download_installer(self.progress_update.emit)
                
            self.progress_update.emit(100)
            
            # Signal manual intervention needed
            # We can't really track the installers progress easily without silent mode
            # But we can just wait for the process to exit.
            
            success = run_installer(installer_path)
            
            if success:
                # Refresh detection
                found = setup_tesseract()
                if found:
                    self.finished.emit(True, "Tesseract installed successfully!")
                else:
                    self.finished.emit(False, "Installer finished, but Tesseract still not found. Did you install it to a custom location?")
            else:
                self.finished.emit(False, "Installation cancelled or failed.")
                
        except Exception as e:
            self.finished.emit(False, str(e))


class OcrWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    progress_update = pyqtSignal(int)
    
    def __init__(self, input_path, output_path, lang='eng'):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.lang = lang

    def run(self):
        try:
            ocr_pdf(
                self.input_path, 
                self.output_path, 
                language=self.lang, 
                progress_callback=self.progress_update.emit
            )
            self.finished.emit(self.output_path)
        except Exception as e:
            self.error.emit(str(e))

class OcrTab(FeatureTab):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_file = None

    def setup_controls(self):
        self.controls_layout.setSpacing(20)

        title = QLabel("OCR (Text Recognition)")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        self.controls_layout.addWidget(title)
        
        description = QLabel("Make scanned documents searchable by adding a text layer.")
        description.setWordWrap(True)
        description.setStyleSheet("color: #C0C0C0;")
        self.controls_layout.addWidget(description)

        self.file_label = QLabel("No file selected.")
        self.controls_layout.addWidget(self.file_label)

        select_button = QPushButton("Select Scanned PDF")
        select_button.clicked.connect(self.select_file)
        self.controls_layout.addWidget(select_button)

        # Language selection
        lang_layout = QVBoxLayout()
        lang_layout.addWidget(QLabel("Language:"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["English (eng)", "Spanish (spa)", "French (fra)", "German (deu)"])
        lang_layout.addWidget(self.lang_combo)
        self.controls_layout.addLayout(lang_layout)

        self.ocr_button = QPushButton("Start OCR")
        self.ocr_button.setObjectName("action_button")
        self.ocr_button.clicked.connect(self.run_ocr)
        self.controls_layout.addWidget(self.ocr_button)
        
        self.controls_layout.addStretch()

    def select_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select PDF", "", "PDF Files (*.pdf)")
        if file:
            self.selected_file = file
            self.file_label.setText(file)
            self.preview.load_pdf(file)

    def run_ocr(self):
        if not self.selected_file:
            QMessageBox.warning(self, "No File Selected", "Please select a PDF file.")
            return

        save_path, _ = QFileDialog.getSaveFileName(self, "Save OCR PDF", "", "PDF Files (*.pdf)")
        if not save_path:
            return

        lang_code = self.lang_combo.currentText().split("(")[1].strip(")")
        
        self.progress = QProgressDialog("Running OCR (this may take a while)...", "Cancel", 0, 100, self)
        self.progress.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress.show()

        self.worker = OcrWorker(self.selected_file, save_path, lang=lang_code)
        self.worker.finished.connect(self.on_ocr_finished)
        self.worker.error.connect(self.on_ocr_error)
        self.worker.progress_update.connect(self.progress.setValue)
        self.worker.start()

    def on_ocr_finished(self, output_path):
        self.progress.cancel()
        QMessageBox.information(self, "Success", f"OCR complete. Saved to:\n{output_path}")

    def on_ocr_error(self, error_msg):
        self.progress.cancel()
        
        if "Tesseract OCR is not found" in error_msg:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("OCR Missing")
            msg.setText("Tesseract OCR is required for this feature.")
            msg.setInformativeText("Would you like to download and install it now?")
            msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg.setDefaultButton(QMessageBox.StandardButton.Yes)
            
            if msg.exec() == QMessageBox.StandardButton.Yes:
                self.install_tesseract()
        else:
            QMessageBox.critical(self, "OCR Failed", f"{error_msg}\n\nMake sure Tesseract-OCR is installed and trained data is available.")

    def install_tesseract(self):
        self.install_progress = QProgressDialog("Downloading Tesseract Installer...", "Cancel", 0, 100, self)
        self.install_progress.setWindowModality(Qt.WindowModality.WindowModal)
        self.install_progress.show()
        
        self.install_worker = InstallTesseractWorker()
        self.install_worker.progress_update.connect(self.install_progress.setValue)
        self.install_worker.finished.connect(self.on_install_finished)
        self.install_worker.start()
        
    def on_install_finished(self, success, message):
        self.install_progress.cancel()
        if success:
            QMessageBox.information(self, "Installation Complete", message + "\n\nPlease try running OCR again.")
        else:
            QMessageBox.warning(self, "Installation Issue", message)
