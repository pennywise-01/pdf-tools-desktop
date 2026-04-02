from PyQt6.QtWidgets import (
    QPushButton, QLabel, QLineEdit, QHBoxLayout, QMessageBox, QFileDialog, QProgressDialog,
    QVBoxLayout
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont

from widgets.feature_tab import FeatureTab, COLORS
from features.remove_pages import remove_pages

class RemovePagesWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, input_path, output_path, pages_to_remove):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.pages_to_remove = pages_to_remove

    def run(self):
        try:
            remove_pages(self.input_path, self.output_path, self.pages_to_remove)
            self.finished.emit(self.output_path)
        except Exception as e:
            self.error.emit(str(e))

class RemovePagesTab(FeatureTab):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_remove_pages_file = None

    def setup_controls(self):
        # Header
        header = self.create_header(
            "Remove Pages",
            "Select a PDF file and choose the pages you want to remove."
        )
        self.controls_layout.addWidget(header)

        # File selection
        self.file_container, self.remove_pages_file_label = self.create_file_label()
        self.controls_layout.addWidget(self.file_container)

        select_button = self.create_secondary_button("Select PDF", self.select_remove_pages_file)
        self.controls_layout.addWidget(select_button)

        # Instructions
        pages_label = self.create_info_label("Select pages to remove from the preview.")
        self.controls_layout.addWidget(pages_label)

        # Action button
        self.remove_button = self.create_danger_button("Remove Pages", self.remove_pages_file)
        self.controls_layout.addWidget(self.remove_button)
        
        self.controls_layout.addStretch()

    def select_remove_pages_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select PDF", "", "PDF Files (*.pdf)")
        if file:
            self.selected_remove_pages_file = file
            filename = file.split('/')[-1].split('\\')[-1]
            self.remove_pages_file_label.setText(filename)
            self.preview.load_pdf(file)

    def remove_pages_file(self):
        if not self.selected_remove_pages_file:
            QMessageBox.warning(self, "No File Selected", "Please select a PDF file.")
            return

        selected_pages = self.preview.get_selected_pages()
        if not selected_pages:
            QMessageBox.warning(self, "No Pages Selected", "Please select pages to remove from the preview.")
            return
            
        pages_to_remove_str = ",".join(map(str, sorted(selected_pages)))

        output_path, _ = QFileDialog.getSaveFileName(self, "Save PDF", "", "PDF Files (*.pdf)")
        if output_path:
            self.progress_dialog = QProgressDialog("Removing pages...", "Cancel", 0, 0, self)
            self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            self.progress_dialog.show()

            self.worker = RemovePagesWorker(self.selected_remove_pages_file, output_path, pages_to_remove_str)
            self.worker.finished.connect(self.on_remove_pages_finished)
            self.worker.error.connect(self.on_remove_pages_error)
            self.worker.start()
            self.remove_button.setEnabled(False)

    def on_remove_pages_finished(self, output_path):
        self.progress_dialog.close()
        QMessageBox.information(self, "Success", f"Successfully removed pages and saved PDF to {output_path}")
        self.preview.clear()
        self.remove_pages_file_label.setText("No file selected.")
        self.selected_remove_pages_file = None
        self.remove_button.setEnabled(True)

    def on_remove_pages_error(self, error_message):
        self.progress_dialog.close()
        self.show_error("An error occurred while removing pages.", error_message, "RMV")
        self.remove_button.setEnabled(True)

    def handle_file_drop(self, files):
        if files:
            file = files[0]
            if file.lower().endswith('.pdf'):
                self.selected_remove_pages_file = file
                filename = file.split('/')[-1].split('\\')[-1]
                self.remove_pages_file_label.setText(filename)
                self.preview.load_pdf(file)