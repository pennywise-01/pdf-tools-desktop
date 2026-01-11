from PyQt6.QtWidgets import (
    QPushButton, QLabel, QLineEdit, QHBoxLayout, QMessageBox, QFileDialog, 
    QProgressDialog, QVBoxLayout, QSlider
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont

from widgets.feature_tab import FeatureTab
from features.watermark import add_watermark

class WatermarkWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, input_path, output_path, text, opacity, rotation):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.text = text
        self.opacity = opacity
        self.rotation = rotation

    def run(self):
        try:
            add_watermark(self.input_path, self.output_path, self.text, self.opacity, self.rotation)
            self.finished.emit(self.output_path)
        except Exception as e:
            self.error.emit(str(e))

class WatermarkTab(FeatureTab):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_file = None

    def setup_controls(self):
        self.controls_layout.setSpacing(20)

        title = QLabel("Add Watermark")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        self.controls_layout.addWidget(title)

        description = QLabel("Add a text watermark to every page of your PDF.")
        description.setWordWrap(True)
        description.setStyleSheet("color: #C0C0C0;")
        self.controls_layout.addWidget(description)

        self.file_label = QLabel("No file selected.")
        self.controls_layout.addWidget(self.file_label)

        select_button = QPushButton("Select PDF")
        select_button.clicked.connect(self.select_file)
        self.controls_layout.addWidget(select_button)

        # Watermark Text
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Enter Watermark Text (e.g., CONFIDENTIAL)")
        self.controls_layout.addWidget(self.text_input)

        # Settings
        settings_layout = QHBoxLayout()
        
        # Opacity
        opacity_layout = QVBoxLayout()
        opacity_layout.addWidget(QLabel("Opacity:"))
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(30)
        opacity_layout.addWidget(self.opacity_slider)
        settings_layout.addLayout(opacity_layout)
        
        # Rotation
        rotation_layout = QVBoxLayout()
        rotation_layout.addWidget(QLabel("Rotation:"))
        self.rotation_input = QLineEdit("45")
        self.rotation_input.setFixedWidth(50)
        rotation_layout.addWidget(self.rotation_input)
        settings_layout.addLayout(rotation_layout)

        self.controls_layout.addLayout(settings_layout)

        self.apply_button = QPushButton("Apply Watermark")
        self.apply_button.setObjectName("apply_button")
        self.apply_button.clicked.connect(self.apply_watermark)
        self.controls_layout.addWidget(self.apply_button)
        
        self.controls_layout.addStretch()

    def select_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select PDF", "", "PDF Files (*.pdf)")
        if file:
            self.selected_file = file
            self.file_label.setText(file)
            self.preview.load_pdf(file)

    def apply_watermark(self):
        if not self.selected_file:
            QMessageBox.warning(self, "No File Selected", "Please select a PDF file.")
            return
        
        text = self.text_input.text()
        if not text:
            QMessageBox.warning(self, "No Text", "Please enter watermark text.")
            return

        try:
            opacity = self.opacity_slider.value() / 100.0
            rotation = int(self.rotation_input.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Rotation must be a number.")
            return

        output_path, _ = QFileDialog.getSaveFileName(self, "Save Watermarked PDF", "", "PDF Files (*.pdf)")
        if output_path:
            self.progress_dialog = QProgressDialog("Adding Watermark...", "Cancel", 0, 0, self)
            self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            self.progress_dialog.show()

            self.worker = WatermarkWorker(self.selected_file, output_path, text, opacity, rotation)
            self.worker.finished.connect(self.on_finished)
            self.worker.error.connect(self.on_error)
            self.worker.start()
            self.apply_button.setEnabled(False)

    def on_finished(self, output_path):
        self.progress_dialog.close()
        QMessageBox.information(self, "Success", f"Watermark added successfully to {output_path}")
        self.preview.clear()
        self.file_label.setText("No file selected.")
        self.selected_file = None
        self.apply_button.setEnabled(True)

    def on_error(self, error_message):
        self.progress_dialog.close()
        self.show_error("An error occurred while adding the watermark.", error_message, "WAT")
        self.apply_button.setEnabled(True)

    def handle_file_drop(self, files):
        if files:
            file = files[0]
            if file.lower().endswith('.pdf'):
                self.selected_file = file
                self.file_label.setText(file)
                self.preview.load_pdf(file)
