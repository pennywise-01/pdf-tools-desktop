from PyQt6.QtWidgets import (
    QPushButton, QLabel, QComboBox, QHBoxLayout, QMessageBox, QFileDialog, 
    QProgressDialog, QVBoxLayout
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont

from widgets.feature_tab import FeatureTab, COLORS
from features.pdf_to_images import convert_pdf_to_images

class PdfToImagesWorker(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, input_path, output_dir, format, dpi):
        super().__init__()
        self.input_path = input_path
        self.output_dir = output_dir
        self.format = format
        self.dpi = dpi

    def run(self):
        try:
            output_files = convert_pdf_to_images(self.input_path, self.output_dir, self.format, self.dpi)
            self.finished.emit(output_files)
        except Exception as e:
            self.error.emit(str(e))

class PdfToImagesTab(FeatureTab):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_file = None

    def setup_controls(self):
        # Header
        header = self.create_header(
            "PDF to Images",
            "Convert PDF pages into high-resolution images."
        )
        self.controls_layout.addWidget(header)

        # File selection
        self.file_container, self.file_label = self.create_file_label()
        self.controls_layout.addWidget(self.file_container)

        select_button = self.create_secondary_button("Select PDF", self.select_file)
        self.controls_layout.addWidget(select_button)

        # Options section
        options_section, options_layout = self.create_section("Output Options")
        
        # Format row
        format_layout = QHBoxLayout()
        format_label = self.create_label("Format:")
        format_layout.addWidget(format_label)
        self.format_combo = self.create_dropdown(["png", "jpg"])
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch()
        options_layout.addLayout(format_layout)
        
        # DPI row
        dpi_layout = QHBoxLayout()
        dpi_label = self.create_label("DPI:")
        dpi_layout.addWidget(dpi_label)
        self.dpi_combo = self.create_dropdown(["72", "150", "300", "600"])
        self.dpi_combo.setCurrentText("300")
        dpi_layout.addWidget(self.dpi_combo)
        dpi_layout.addStretch()
        options_layout.addLayout(dpi_layout)
        
        self.controls_layout.addWidget(options_section)

        # Action button
        self.convert_button = self.create_primary_button("Convert to Images", self.convert_file)
        self.controls_layout.addWidget(self.convert_button)
        
        self.controls_layout.addStretch()

    def select_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select PDF", "", "PDF Files (*.pdf)")
        if file:
            self.selected_file = file
            filename = file.split('/')[-1].split('\\')[-1]
            self.file_label.setText(filename)
            self.preview.load_pdf(file)

    def convert_file(self):
        if not self.selected_file:
            QMessageBox.warning(self, "No File Selected", "Please select a PDF file.")
            return

        output_dir = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if output_dir:
            format = self.format_combo.currentText()
            dpi = int(self.dpi_combo.currentText())

            self.progress_dialog = QProgressDialog("Converting PDF to Images...", "Cancel", 0, 0, self)
            self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            self.progress_dialog.show()

            self.worker = PdfToImagesWorker(self.selected_file, output_dir, format, dpi)
            self.worker.finished.connect(self.on_convert_finished)
            self.worker.error.connect(self.on_convert_error)
            self.worker.start()
            self.convert_button.setEnabled(False)

    def on_convert_finished(self, output_files):
        self.progress_dialog.close()
        QMessageBox.information(self, "Success", f"Successfully converted {len(output_files)} pages to images in selected directory.")
        self.convert_button.setEnabled(True)

    def on_convert_error(self, error_message):
        self.progress_dialog.close()
        self.show_error("An error occurred during conversion.", error_message, "P2I")
        self.convert_button.setEnabled(True)

    def handle_file_drop(self, files):
        if files:
            file = files[0]
            if file.lower().endswith('.pdf'):
                self.selected_file = file
                filename = file.split('/')[-1].split('\\')[-1]
                self.file_label.setText(filename)
                self.preview.load_pdf(file)
