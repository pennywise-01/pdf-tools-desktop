from PyQt6.QtWidgets import (
    QPushButton, QLabel, QHBoxLayout, QMessageBox, QFileDialog, 
    QProgressDialog, QVBoxLayout, QSlider
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont

from widgets.feature_tab import FeatureTab
from features.compress_pdf import compress_pdf

class CompressWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, input_path, output_path, quality):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.quality = quality

    def run(self):
        try:
            compress_pdf(self.input_path, self.output_path, self.quality)
            self.finished.emit(self.output_path)
        except Exception as e:
            self.error.emit(str(e))

class CompressTab(FeatureTab):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_file = None

    def setup_controls(self):
        self.controls_layout.setSpacing(20)

        title = QLabel("Compress PDF")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        self.controls_layout.addWidget(title)

        description = QLabel("Reduce the file size of your PDF.")
        description.setWordWrap(True)
        description.setStyleSheet("color: #C0C0C0;")
        self.controls_layout.addWidget(description)

        self.file_label = QLabel("No file selected.")
        self.controls_layout.addWidget(self.file_label)

        select_button = QPushButton("Select PDF")
        select_button.clicked.connect(self.select_file)
        self.controls_layout.addWidget(select_button)

        # Compression Level
        level_layout = QVBoxLayout()
        level_layout.addWidget(QLabel("Compression Level:"))
        
        self.level_slider = QSlider(Qt.Orientation.Horizontal)
        self.level_slider.setRange(0, 4)
        self.level_slider.setValue(4)
        self.level_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.level_slider.setTickInterval(1)
        self.level_slider.valueChanged.connect(self.update_level_label)
        level_layout.addWidget(self.level_slider)
        
        self.level_label = QLabel("Maximum (Best Compression)")
        level_layout.addWidget(self.level_label)
        
        self.controls_layout.addLayout(level_layout)

        self.compress_button = QPushButton("Compress PDF")
        self.compress_button.setObjectName("compress_button")
        self.compress_button.clicked.connect(self.compress_file)
        self.controls_layout.addWidget(self.compress_button)
        
        self.controls_layout.addStretch()

    def update_level_label(self, value):
        labels = {
            0: "None (Just Copy)",
            1: "Low (Clean Objects)",
            2: "Medium (Deflate Streams)",
            3: "High (Deduplicate)",
            4: "Maximum (Best Compression)"
        }
        self.level_label.setText(labels.get(value, "Unknown"))

    def select_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select PDF", "", "PDF Files (*.pdf)")
        if file:
            self.selected_file = file
            self.file_label.setText(file)
            self.preview.load_pdf(file)

    def compress_file(self):
        if not self.selected_file:
            QMessageBox.warning(self, "No File Selected", "Please select a PDF file.")
            return

        quality = self.level_slider.value()

        output_path, _ = QFileDialog.getSaveFileName(self, "Save Compressed PDF", "", "PDF Files (*.pdf)")
        if output_path:
            self.progress_dialog = QProgressDialog("Compressing PDF...", "Cancel", 0, 0, self)
            self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            self.progress_dialog.show()

            self.worker = CompressWorker(self.selected_file, output_path, quality)
            self.worker.finished.connect(self.on_finished)
            self.worker.error.connect(self.on_error)
            self.worker.start()
            self.compress_button.setEnabled(False)

    def on_finished(self, output_path):
        self.progress_dialog.close()
        QMessageBox.information(self, "Success", f"PDF compressed successfully to {output_path}")
        self.preview.clear()
        self.file_label.setText("No file selected.")
        self.selected_file = None
        self.compress_button.setEnabled(True)

    def on_error(self, error_message):
        self.progress_dialog.close()
        self.show_error("An error occurred while compressing the PDF.", error_message, "CMP")
        self.compress_button.setEnabled(True)

    def handle_file_drop(self, files):
        if files:
            file = files[0]
            if file.lower().endswith('.pdf'):
                self.selected_file = file
                self.file_label.setText(file)
                self.preview.load_pdf(file)
