from PyQt6.QtWidgets import (
    QPushButton, QLabel, QLineEdit, QHBoxLayout, QMessageBox, QComboBox, QFileDialog, 
    QProgressDialog, QVBoxLayout
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont

from widgets.feature_tab import FeatureTab, COLORS
from features.rotate_pages import rotate_pages

class RotateWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, input_path, output_path, page_number, angle):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.page_number = page_number
        self.angle = angle

    def run(self):
        try:
            rotate_pages(self.input_path, self.output_path, self.page_number, self.angle)
            self.finished.emit(self.output_path)
        except Exception as e:
            self.error.emit(str(e))

class RotatePagesTab(FeatureTab):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_rotate_pages_file = None

    def setup_controls(self):
        # Header
        header = self.create_header(
            "Rotate Pages",
            "Select a PDF file and choose a page and rotation angle."
        )
        self.controls_layout.addWidget(header)

        # File selection
        self.file_container, self.rotate_pages_file_label = self.create_file_label()
        self.controls_layout.addWidget(self.file_container)

        select_button = self.create_secondary_button("Select PDF", self.select_rotate_pages_file)
        self.controls_layout.addWidget(select_button)

        # Rotation options section
        options_section, options_layout = self.create_section("Rotation Options")
        
        # Page number
        page_layout = QHBoxLayout()
        page_label = self.create_label("Page Number:")
        page_layout.addWidget(page_label)
        self.rotate_page_number_input = self.create_input("Enter page number")
        page_layout.addWidget(self.rotate_page_number_input)
        options_layout.addLayout(page_layout)

        # Angle
        angle_layout = QHBoxLayout()
        angle_label = self.create_label("Rotation Angle:")
        angle_layout.addWidget(angle_label)
        self.rotate_angle_input = self.create_dropdown(["90", "180", "270"])
        angle_layout.addWidget(self.rotate_angle_input)
        angle_layout.addStretch()
        options_layout.addLayout(angle_layout)
        
        self.controls_layout.addWidget(options_section)

        # Action button
        self.rotate_button = self.create_primary_button("Rotate Page", self.rotate_page)
        self.controls_layout.addWidget(self.rotate_button)
        
        self.controls_layout.addStretch()

    def select_rotate_pages_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select PDF", "", "PDF Files (*.pdf)")
        if file:
            self.selected_rotate_pages_file = file
            filename = file.split('/')[-1].split('\\')[-1]
            self.rotate_pages_file_label.setText(filename)
            self.preview.load_pdf(file)

    def rotate_page(self):
        if not self.selected_rotate_pages_file:
            QMessageBox.warning(self, "No File Selected", "Please select a PDF file to rotate.")
            return

        try:
            page_number = int(self.rotate_page_number_input.text())
            angle = int(self.rotate_angle_input.currentText())
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid page number.")
            return

        output_path, _ = QFileDialog.getSaveFileName(self, "Save Rotated PDF", "", "PDF Files (*.pdf)")
        if output_path:
            self.progress_dialog = QProgressDialog("Rotating page...", "Cancel", 0, 0, self)
            self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            self.progress_dialog.show()

            self.worker = RotateWorker(self.selected_rotate_pages_file, output_path, page_number, angle)
            self.worker.finished.connect(self.on_rotate_finished)
            self.worker.error.connect(self.on_rotate_error)
            self.worker.start()
            self.rotate_button.setEnabled(False)

    def on_rotate_finished(self, output_path):
        self.progress_dialog.close()
        QMessageBox.information(self, "Success", f"Successfully rotated page and saved to {output_path}")
        self.preview.clear()
        self.rotate_pages_file_label.setText("No file selected.")
        self.selected_rotate_pages_file = None
        self.rotate_page_number_input.clear()
        self.rotate_button.setEnabled(True)

    def on_rotate_error(self, error_message):
        self.progress_dialog.close()
        self.show_error("An error occurred while rotating the page.", error_message, "ROT")
        self.rotate_button.setEnabled(True)

    def handle_file_drop(self, files):
        if files:
            file = files[0]
            if file.lower().endswith('.pdf'):
                self.selected_rotate_pages_file = file
                filename = file.split('/')[-1].split('\\')[-1]
                self.rotate_pages_file_label.setText(filename)
                self.preview.load_pdf(file)
