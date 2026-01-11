from PyQt6.QtWidgets import (
    QPushButton, QLabel, QLineEdit, QHBoxLayout, QMessageBox, QComboBox, QFileDialog, 
    QProgressDialog, QVBoxLayout
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont

from widgets.feature_tab import FeatureTab
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
        self.controls_layout.setSpacing(20)

        title = QLabel("Rotate Pages")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        self.controls_layout.addWidget(title)

        description = QLabel("Select a PDF file and choose a page and rotation angle.")
        description.setWordWrap(True)
        description.setStyleSheet("color: #C0C0C0;")
        self.controls_layout.addWidget(description)

        self.rotate_pages_file_label = QLabel("No file selected.")
        self.controls_layout.addWidget(self.rotate_pages_file_label)

        select_button = QPushButton("Select PDF")
        select_button.clicked.connect(self.select_rotate_pages_file)
        self.controls_layout.addWidget(select_button)

        page_number_layout = QHBoxLayout()
        page_number_label = QLabel("Page Number:")
        page_number_layout.addWidget(page_number_label)
        self.rotate_page_number_input = QLineEdit()
        page_number_layout.addWidget(self.rotate_page_number_input)
        self.controls_layout.addLayout(page_number_layout)

        angle_layout = QHBoxLayout()
        angle_label = QLabel("Rotation Angle:")
        angle_layout.addWidget(angle_label)
        self.rotate_angle_input = QComboBox()
        self.rotate_angle_input.addItems(["90", "180", "270"])
        angle_layout.addWidget(self.rotate_angle_input)
        self.controls_layout.addLayout(angle_layout)

        self.rotate_button = QPushButton("Rotate Page")
        self.rotate_button.setObjectName("rotate_button")
        self.rotate_button.clicked.connect(self.rotate_page)
        self.controls_layout.addWidget(self.rotate_button)
        
        self.controls_layout.addStretch()

    def select_rotate_pages_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select PDF", "", "PDF Files (*.pdf)")
        if file:
            self.selected_rotate_pages_file = file
            self.rotate_pages_file_label.setText(file)
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
                self.rotate_pages_file_label.setText(file)
                self.preview.load_pdf(file)
