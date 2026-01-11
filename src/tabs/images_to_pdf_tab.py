from PyQt6.QtWidgets import (
    QPushButton, QListWidget, QMessageBox, QFileDialog, QProgressDialog,
    QVBoxLayout, QLabel, QWidget
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont

from widgets.feature_tab import FeatureTab
from features.images_to_pdf import convert_images_to_pdf

class ImagesToPdfWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, input_paths, output_path):
        super().__init__()
        self.input_paths = input_paths
        self.output_path = output_path

    def run(self):
        try:
            convert_images_to_pdf(self.input_paths, self.output_path)
            self.finished.emit(self.output_path)
        except Exception as e:
            self.error.emit(str(e))

class ImagesToPdfTab(FeatureTab):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_image_files = []
        
    def setup_controls(self):
        self.controls_layout.setSpacing(20)

        title = QLabel("Images to PDF")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        self.controls_layout.addWidget(title)

        description = QLabel("Select multiple JPG or PNG images to combine them into a single PDF file.")
        description.setWordWrap(True)
        description.setStyleSheet("color: #C0C0C0;")
        self.controls_layout.addWidget(description)

        self.image_file_list = QListWidget()
        self.controls_layout.addWidget(self.image_file_list)

        buttons_layout = QVBoxLayout()
        select_button = QPushButton("Select Images")
        select_button.clicked.connect(self.select_image_files)
        buttons_layout.addWidget(select_button)

        self.convert_button = QPushButton("Convert to PDF")
        self.convert_button.setObjectName("convert_button")
        self.convert_button.clicked.connect(self.convert_files)
        buttons_layout.addWidget(self.convert_button)

        self.clear_button = QPushButton("Clear")
        self.clear_button.setObjectName("clear_button")
        self.clear_button.clicked.connect(self.clear_image_list)
        buttons_layout.addWidget(self.clear_button)

        self.controls_layout.addLayout(buttons_layout)

    def select_image_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Images to Convert", "", "Image Files (*.jpg *.png)")
        if files:
            self.selected_image_files.extend(files)
            self.image_file_list.addItems(files)

    def convert_files(self):
        if len(self.selected_image_files) < 1:
            QMessageBox.warning(self, "Not Enough Files", "Please select at least one image file to convert.")
            return

        output_path, _ = QFileDialog.getSaveFileName(self, "Save PDF", "", "PDF Files (*.pdf)")
        if output_path:
            self.progress_dialog = QProgressDialog("Converting Images to PDF...", "Cancel", 0, 0, self)
            self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            self.progress_dialog.show()

            self.worker = ImagesToPdfWorker(self.selected_image_files, output_path)
            self.worker.finished.connect(self.on_conversion_finished)
            self.worker.error.connect(self.on_conversion_error)
            self.worker.start()
            self.convert_button.setEnabled(False)
            self.clear_button.setEnabled(False)

    def on_conversion_finished(self, output_path):
        self.progress_dialog.close()
        QMessageBox.information(self, "Success", f"Successfully converted images to {output_path}")
        self.clear_image_list()
        self.convert_button.setEnabled(True)
        self.clear_button.setEnabled(True)

    def on_conversion_error(self, error_message):
        self.progress_dialog.close()
        self.show_error("An error occurred while converting images.", error_message, "IMG")
        self.convert_button.setEnabled(True)
        self.clear_button.setEnabled(True)

    def clear_image_list(self):
        self.selected_image_files.clear()
        self.image_file_list.clear()
        self.preview.clear()

    def handle_file_drop(self, files):
        image_files = [f for f in files if f.lower().endswith(('.jpg', '.png'))]
        if image_files:
            self.selected_image_files.extend(image_files)
            self.image_file_list.addItems(image_files)
