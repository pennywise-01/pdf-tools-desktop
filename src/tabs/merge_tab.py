from PyQt6.QtWidgets import (
    QPushButton, QListWidget, QMessageBox, QFileDialog, QProgressDialog,
    QVBoxLayout, QLabel, QWidget, QHBoxLayout
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont

from widgets.feature_tab import FeatureTab, COLORS
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
        # Header
        header = self.create_header(
            "Merge PDFs",
            "Combine multiple PDF files into a single document. Click items to preview."
        )
        self.controls_layout.addWidget(header)

        # File list
        self.merge_file_list = self.create_list_widget(220)
        self.merge_file_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.merge_file_list.itemClicked.connect(self.show_merge_preview)
        self.controls_layout.addWidget(self.merge_file_list)
        
        # File count label
        self.file_count_label = self.create_label("0 files selected", secondary=True)
        self.controls_layout.addWidget(self.file_count_label)

        # Buttons layout
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(12)
        
        select_button = self.create_secondary_button("Select PDFs", self.select_merge_files)
        buttons_layout.addWidget(select_button)

        self.merge_button = self.create_primary_button("Merge PDFs", self.merge_files)
        buttons_layout.addWidget(self.merge_button)

        self.clear_button = self.create_danger_button("Clear All", self.clear_merge_list)
        buttons_layout.addWidget(self.clear_button)

        self.controls_layout.addLayout(buttons_layout)
        self.controls_layout.addStretch()

    def select_merge_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select PDFs to Merge", "", "PDF Files (*.pdf)")
        if files:
            self.selected_merge_files.extend(files)
            self.merge_file_list.addItems([f.split('/')[-1].split('\\')[-1] for f in files])
            self.update_file_count()

    def update_file_count(self):
        count = len(self.selected_merge_files)
        self.file_count_label.setText(f"{count} file{'s' if count != 1 else ''} selected")

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
        self.update_file_count()

    def show_merge_preview(self, item):
        idx = self.merge_file_list.row(item)
        if idx < len(self.selected_merge_files):
            self.preview.load_pdf(self.selected_merge_files[idx])

    def handle_file_drop(self, files):
        pdf_files = [f for f in files if f.lower().endswith('.pdf')]
        if pdf_files:
            self.selected_merge_files.extend(pdf_files)
            self.merge_file_list.addItems(pdf_files)
