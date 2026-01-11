from PyQt6.QtWidgets import (
    QPushButton, QLabel, QLineEdit, QHBoxLayout, QMessageBox, QFileDialog, QProgressDialog,
    QVBoxLayout
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont

from widgets.feature_tab import FeatureTab
from features.split_pdf import split_pdf

def to_range_string(numbers):
    if not numbers:
        return ""
    numbers = sorted(list(set(numbers)))
    ranges = []
    start = end = numbers[0]
    for n in numbers[1:]:
        if n == end + 1:
            end = n
        else:
            if start == end:
                ranges.append(str(start))
            else:
                ranges.append(f"{start}-{end}")
            start = end = n
    if start == end:
        ranges.append(str(start))
    else:
        ranges.append(f"{start}-{end}")
    return ",".join(ranges)

class ExtractPagesWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, input_path, output_path, page_range):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.page_range = page_range

    def run(self):
        try:
            split_pdf(self.input_path, self.output_path, self.page_range)
            self.finished.emit(self.output_path)
        except Exception as e:
            self.error.emit(str(e))

class ExtractPagesTab(FeatureTab):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_extract_pages_file = None

    def setup_controls(self):
        self.controls_layout.setSpacing(20)

        title = QLabel("Extract Pages")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        self.controls_layout.addWidget(title)

        description = QLabel("Select a PDF file and choose the pages you want to extract into a new file.")
        description.setWordWrap(True)
        description.setStyleSheet("color: #C0C0C0;")
        self.controls_layout.addWidget(description)

        self.extract_pages_file_label = QLabel("No file selected.")
        self.controls_layout.addWidget(self.extract_pages_file_label)

        select_button = QPushButton("Select PDF")
        select_button.clicked.connect(self.select_extract_pages_file)
        self.controls_layout.addWidget(select_button)

        pages_label = QLabel("Select pages to extract from the preview.")
        self.controls_layout.addWidget(pages_label)

        self.extract_button = QPushButton("Extract Pages")
        self.extract_button.setObjectName("extract_button")
        self.extract_button.clicked.connect(self.extract_pages)
        self.controls_layout.addWidget(self.extract_button)
        
        self.controls_layout.addStretch()


    def select_extract_pages_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select PDF to Extract Pages from", "", "PDF Files (*.pdf)")
        if file:
            self.selected_extract_pages_file = file
            self.extract_pages_file_label.setText(file)
            self.preview.load_pdf(file)

    def extract_pages(self):
        if not self.selected_extract_pages_file:
            QMessageBox.warning(self, "No File Selected", "Please select a PDF file to extract pages from.")
            return

        selected_pages = self.preview.get_selected_pages()
        if not selected_pages:
            QMessageBox.warning(self, "No Pages Selected", "Please select pages to extract from the preview.")
            return

        page_range_str = to_range_string(selected_pages)

        output_path, _ = QFileDialog.getSaveFileName(self, "Save Extracted PDF", "", "PDF Files (*.pdf)")
        if output_path:
            self.progress_dialog = QProgressDialog("Extracting pages...", "Cancel", 0, 0, self)
            self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            self.progress_dialog.show()

            self.worker = ExtractPagesWorker(self.selected_extract_pages_file, output_path, page_range_str)
            self.worker.finished.connect(self.on_extract_finished)
            self.worker.error.connect(self.on_extract_error)
            self.worker.start()
            self.extract_button.setEnabled(False)

    def on_extract_finished(self, output_path):
        self.progress_dialog.close()
        QMessageBox.information(self, "Success", f"Successfully extracted pages to {output_path}")
        self.preview.clear()
        self.extract_pages_file_label.setText("No file selected.")
        self.selected_extract_pages_file = None
        self.extract_button.setEnabled(True)

    def on_extract_error(self, error_message):
        self.progress_dialog.close()
        self.show_error("An error occurred while extracting pages.", error_message, "EXT")
        self.extract_button.setEnabled(True)

    def handle_file_drop(self, files):
        if files:
            file = files[0]
            if file.lower().endswith('.pdf'):
                self.selected_extract_pages_file = file
                self.extract_pages_file_label.setText(file)
                self.preview.load_pdf(file)