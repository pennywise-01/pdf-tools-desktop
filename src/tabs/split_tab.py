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

class SplitWorker(QThread):
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

class SplitTab(FeatureTab):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_split_file = None

    def setup_controls(self):
        self.controls_layout.setSpacing(20)

        title = QLabel("Split PDF")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        self.controls_layout.addWidget(title)

        description = QLabel("Select a PDF file and choose the pages you want to extract into a new file.")
        description.setWordWrap(True)
        description.setStyleSheet("color: #C0C0C0;")
        self.controls_layout.addWidget(description)

        self.split_file_label = QLabel("No file selected.")
        self.controls_layout.addWidget(self.split_file_label)
        
        select_button = QPushButton("Select PDF")
        select_button.clicked.connect(self.select_split_file)
        self.controls_layout.addWidget(select_button)

        pages_label = QLabel("Select pages to split from the preview.")
        self.controls_layout.addWidget(pages_label)

        self.split_button = QPushButton("Split PDF")
        self.split_button.setObjectName("split_button")
        self.split_button.clicked.connect(self.split_file)
        self.controls_layout.addWidget(self.split_button)
        
        self.controls_layout.addStretch()

    def select_split_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select PDF to Split", "", "PDF Files (*.pdf)")
        if file:
            self.selected_split_file = file
            self.split_file_label.setText(file)
            self.preview.load_pdf(file)

    def split_file(self):
        if not self.selected_split_file:
            QMessageBox.warning(self, "No File Selected", "Please select a PDF file to split.")
            return

        selected_pages = self.preview.get_selected_pages()
        if not selected_pages:
            QMessageBox.warning(self, "No Pages Selected", "Please select pages to split from the preview.")
            return

        page_range_str = to_range_string(selected_pages)

        output_path, _ = QFileDialog.getSaveFileName(self, "Save Split PDF", "", "PDF Files (*.pdf)")
        if output_path:
            self.progress_dialog = QProgressDialog("Splitting PDF...", "Cancel", 0, 0, self)
            self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            self.progress_dialog.show()

            self.worker = SplitWorker(self.selected_split_file, output_path, page_range_str)
            self.worker.finished.connect(self.on_split_finished)
            self.worker.error.connect(self.on_split_error)
            self.worker.start()
            self.split_button.setEnabled(False)

    def on_split_finished(self, output_path):
        self.progress_dialog.close()
        QMessageBox.information(self, "Success", f"Successfully split PDF to {output_path}")
        self.preview.clear()
        self.split_file_label.setText("No file selected.")
        self.selected_split_file = None
        self.split_button.setEnabled(True)

    def on_split_error(self, error_message):
        self.progress_dialog.close()
        self.show_error("An error occurred while splitting the PDF.", error_message, "SPL")
        self.split_button.setEnabled(True)

    def handle_file_drop(self, files):
        if files:
            file = files[0]
            if file.lower().endswith('.pdf'):
                self.selected_split_file = file
                self.split_file_label.setText(file)
                self.preview.load_pdf(file)