from PyQt6.QtWidgets import (
    QPushButton, QLabel, QLineEdit, QHBoxLayout, QMessageBox, QFileDialog, 
    QProgressDialog, QVBoxLayout, QSlider
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont

from widgets.feature_tab import FeatureTab, COLORS
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
        # Header
        header = self.create_header(
            "Add Watermark",
            "Add a text watermark to every page of your PDF."
        )
        self.controls_layout.addWidget(header)

        # File selection
        self.file_container, self.file_label = self.create_file_label()
        self.controls_layout.addWidget(self.file_container)

        select_button = self.create_secondary_button("Select PDF", self.select_file)
        self.controls_layout.addWidget(select_button)

        # Watermark settings section
        watermark_section, watermark_layout = self.create_section("Watermark Settings")
        
        # Watermark Text
        text_label = self.create_label("Watermark Text:")
        watermark_layout.addWidget(text_label)
        
        self.text_input = self.create_input("Enter Watermark Text (e.g., CONFIDENTIAL)")
        watermark_layout.addWidget(self.text_input)

        # Settings row
        settings_layout = QHBoxLayout()
        
        # Opacity
        opacity_container = QVBoxLayout()
        opacity_label = self.create_label("Opacity:")
        opacity_container.addWidget(opacity_label)
        self.opacity_slider = self.create_slider(0, 100, 30)
        opacity_container.addWidget(self.opacity_slider)
        settings_layout.addLayout(opacity_container)
        
        # Rotation
        rotation_container = QVBoxLayout()
        rotation_label = self.create_label("Rotation:")
        rotation_container.addWidget(rotation_label)
        self.rotation_input = self.create_input("45")
        self.rotation_input.setFixedWidth(80)
        rotation_container.addWidget(self.rotation_input)
        settings_layout.addLayout(rotation_container)
        settings_layout.addStretch()
        
        watermark_layout.addLayout(settings_layout)
        self.controls_layout.addWidget(watermark_section)

        # Action button
        self.apply_button = self.create_primary_button("Apply Watermark", self.apply_watermark)
        self.controls_layout.addWidget(self.apply_button)
        
        self.controls_layout.addStretch()

    def select_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select PDF", "", "PDF Files (*.pdf)")
        if file:
            self.selected_file = file
            filename = file.split('/')[-1].split('\\')[-1]
            self.file_label.setText(filename)
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
                filename = file.split('/')[-1].split('\\')[-1]
                self.file_label.setText(filename)
                self.preview.load_pdf(file)
