from PyQt6.QtWidgets import (
    QPushButton, QListWidget, QMessageBox, QFileDialog, QProgressDialog,
    QVBoxLayout, QLabel, QWidget
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont

from widgets.feature_tab import FeatureTab
from features.merge_pdf import merge_pdfs

class MergeWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, input_paths, output_path):
        super().__init__()
        self.input_paths = input_paths
        self.output_path = output_path

    def run(self):
        try:
            merge_pdfs(self.input_paths, self.output_path)
            self.finished.emit(self.output_path)
        except Exception as e:
            self.error.emit(str(e))

class MergeTab(FeatureTab):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_merge_files = []
        
    def setup_controls(self):
        self.controls_layout.setSpacing(20)

        title = QLabel("Merge PDFs")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        self.controls_layout.addWidget(title)

        description = QLabel("Select multiple PDF files to combine them into a single file.")
        description.setWordWrap(True)
        description.setStyleSheet("color: #C0C0C0;")
        self.controls_layout.addWidget(description)

        self.merge_file_list = QListWidget()
        self.merge_file_list.itemClicked.connect(self.show_merge_preview)
        self.controls_layout.addWidget(self.merge_file_list)

        buttons_layout = QVBoxLayout()
        select_button = QPushButton("Select PDFs")
        select_button.clicked.connect(self.select_merge_files)
        buttons_layout.addWidget(select_button)

        self.merge_button = QPushButton("Merge PDFs")
        self.merge_button.setObjectName("merge_button")
        self.merge_button.clicked.connect(self.merge_files)
        buttons_layout.addWidget(self.merge_button)

        self.clear_button = QPushButton("Clear")
        self.clear_button.setObjectName("clear_button")
        self.clear_button.clicked.connect(self.clear_merge_list)
        buttons_layout.addWidget(self.clear_button)

        self.controls_layout.addLayout(buttons_layout)

    def select_merge_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select PDFs to Merge", "", "PDF Files (*.pdf)")
        if files:
            self.selected_merge_files.extend(files)
            self.merge_file_list.addItems(files)

    def merge_files(self):
        if len(self.selected_merge_files) < 2:
            QMessageBox.warning(self, "Not Enough Files", "Please select at least two PDF files to merge.")
            return

        output_path, _ = QFileDialog.getSaveFileName(self, "Save Merged PDF", "", "PDF Files (*.pdf)")
        if output_path:
            self.progress_dialog = QProgressDialog("Merging PDFs...", "Cancel", 0, 0, self)
            self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            self.progress_dialog.show()

            self.worker = MergeWorker(self.selected_merge_files, output_path)
            self.worker.finished.connect(self.on_merge_finished)
            self.worker.error.connect(self.on_merge_error)
            self.worker.start()
            self.merge_button.setEnabled(False)
            self.clear_button.setEnabled(False)

    def on_merge_finished(self, output_path):
        self.progress_dialog.close()
        QMessageBox.information(self, "Success", f"Successfully merged PDFs to {output_path}")
        self.clear_merge_list()
        self.merge_button.setEnabled(True)
        self.clear_button.setEnabled(True)

    def on_merge_error(self, error_message):
        self.progress_dialog.close()
        self.show_error("An error occurred while merging PDFs.", error_message, "MRG")
        self.merge_button.setEnabled(True)
        self.clear_button.setEnabled(True)

    def clear_merge_list(self):
        self.selected_merge_files.clear()
        self.merge_file_list.clear()
        self.preview.clear()

    def show_merge_preview(self, item):
        self.preview.load_pdf(item.text())

    def handle_file_drop(self, files):
        pdf_files = [f for f in files if f.lower().endswith('.pdf')]
        if pdf_files:
            self.selected_merge_files.extend(pdf_files)
            self.merge_file_list.addItems(pdf_files)
