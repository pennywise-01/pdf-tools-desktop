from PyQt6.QtWidgets import (
    QPushButton, QLabel, QLineEdit, QHBoxLayout, QMessageBox, QFileDialog, QProgressDialog,
    QVBoxLayout
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont

from widgets.feature_tab import FeatureTab, COLORS
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
        # Header
        header = self.create_header(
            "Split PDF",
            "Extract specific pages into a new PDF document."
        )
        self.controls_layout.addWidget(header)

        # File selection
        self.file_container, self.file_label = self.create_file_label()
        self.controls_layout.addWidget(self.file_container)
        
        select_button = self.create_secondary_button("Select PDF", self.select_split_file)
        self.controls_layout.addWidget(select_button)

        # Info section
        info_label = self.create_info_label(
            "Click on page thumbnails in the preview to select the pages you want to extract."
        )
        self.controls_layout.addWidget(info_label)

        # Selected pages indicator
        self.pages_label = self.create_label("No pages selected", secondary=True)
        self.controls_layout.addWidget(self.pages_label)

        # Action button
        self.split_button = self.create_primary_button("Split PDF", self.split_file)
        self.controls_layout.addWidget(self.split_button)
        
        self.controls_layout.addStretch()

    def select_split_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select PDF to Split", "", "PDF Files (*.pdf)")
        if file:
            self.selected_split_file = file
            filename = file.split('/')[-1].split('\\')[-1]
            self.file_label.setText(filename)
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
        self.file_label.setText("No file selected.")
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
                filename = file.split('/')[-1].split('\\')[-1]
                self.file_label.setText(filename)
                self.preview.load_pdf(file)