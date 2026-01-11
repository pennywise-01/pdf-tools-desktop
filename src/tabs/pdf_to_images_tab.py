from PyQt6.QtWidgets import (
    QPushButton, QLabel, QComboBox, QHBoxLayout, QMessageBox, QFileDialog, 
    QProgressDialog, QVBoxLayout
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont

from widgets.feature_tab import FeatureTab
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
        self.controls_layout.setSpacing(20)

        title = QLabel("PDF to Images")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        self.controls_layout.addWidget(title)

        description = QLabel("Convert PDF pages into high-resolution images.")
        description.setWordWrap(True)
        description.setStyleSheet("color: #C0C0C0;")
        self.controls_layout.addWidget(description)

        self.file_label = QLabel("No file selected.")
        self.controls_layout.addWidget(self.file_label)

        select_button = QPushButton("Select PDF")
        select_button.clicked.connect(self.select_file)
        self.controls_layout.addWidget(select_button)

        # Options
        options_layout = QHBoxLayout()
        
        # Format
        format_layout = QVBoxLayout()
        format_label = QLabel("Format:")
        self.format_combo = QComboBox()
        self.format_combo.addItems(["png", "jpg"])
        format_layout.addWidget(format_label)
        format_layout.addWidget(self.format_combo)
        options_layout.addLayout(format_layout)
        
        # DPI
        dpi_layout = QVBoxLayout()
        dpi_label = QLabel("DPI:")
        self.dpi_combo = QComboBox()
        self.dpi_combo.addItems(["72", "150", "300", "600"])
        self.dpi_combo.setCurrentText("300")
        dpi_layout.addWidget(dpi_label)
        dpi_layout.addWidget(self.dpi_combo)
        options_layout.addLayout(dpi_layout)
        
        self.controls_layout.addLayout(options_layout)

        self.convert_button = QPushButton("Convert to Images")
        self.convert_button.setObjectName("convert_button")
        self.convert_button.clicked.connect(self.convert_file)
        self.controls_layout.addWidget(self.convert_button)
        
        self.controls_layout.addStretch()

    def select_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select PDF", "", "PDF Files (*.pdf)")
        if file:
            self.selected_file = file
            self.file_label.setText(file)
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
                self.file_label.setText(file)
                self.preview.load_pdf(file)
