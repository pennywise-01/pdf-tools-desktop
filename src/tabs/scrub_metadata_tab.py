from PyQt6.QtWidgets import (
    QPushButton, QLabel, QMessageBox, QFileDialog, QProgressDialog,
    QVBoxLayout
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont

from widgets.feature_tab import FeatureTab, COLORS
from features.scrub_metadata import scrub_metadata

class ScrubWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, input_path, output_path):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path

    def run(self):
        try:
            scrub_metadata(self.input_path, self.output_path)
            self.finished.emit(self.output_path)
        except Exception as e:
            self.error.emit(str(e))

class ScrubMetadataTab(FeatureTab):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_scrub_metadata_file = None

    def setup_controls(self):
        # Header
        header = self.create_header(
            "Scrub Metadata",
            "Select a PDF file to remove all metadata from it."
        )
        self.controls_layout.addWidget(header)

        # File selection
        self.file_container, self.scrub_metadata_file_label = self.create_file_label()
        self.controls_layout.addWidget(self.file_container)

        select_button = self.create_secondary_button("Select PDF", self.select_scrub_metadata_file)
        self.controls_layout.addWidget(select_button)

        # Action button
        self.scrub_button = self.create_primary_button("Scrub Metadata", self.scrub_file_metadata)
        self.controls_layout.addWidget(self.scrub_button)
        
        self.controls_layout.addStretch()

    def select_scrub_metadata_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select PDF to Scrub", "", "PDF Files (*.pdf)")
        if file:
            self.selected_scrub_metadata_file = file
            filename = file.split('/')[-1].split('\\')[-1]
            self.scrub_metadata_file_label.setText(filename)
            self.preview.load_pdf(file)

    def scrub_file_metadata(self):
        if not self.selected_scrub_metadata_file:
            QMessageBox.warning(self, "No File Selected", "Please select a PDF file to scrub.")
            return

        output_path, _ = QFileDialog.getSaveFileName(self, "Save Scrubbed PDF", "", "PDF Files (*.pdf)")
        if output_path:
            self.progress_dialog = QProgressDialog("Scrubbing metadata...", "Cancel", 0, 0, self)
            self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            self.progress_dialog.show()

            self.worker = ScrubWorker(self.selected_scrub_metadata_file, output_path)
            self.worker.finished.connect(self.on_scrub_finished)
            self.worker.error.connect(self.on_scrub_error)
            self.worker.start()
            self.scrub_button.setEnabled(False)

    def on_scrub_finished(self, output_path):
        self.progress_dialog.close()
        QMessageBox.information(self, "Success", f"Successfully scrubbed metadata and saved to {output_path}")
        self.preview.clear()
        self.scrub_metadata_file_label.setText("No file selected.")
        self.selected_scrub_metadata_file = None
        self.scrub_button.setEnabled(True)

    def on_scrub_error(self, error_message):
        self.progress_dialog.close()
        self.show_error("An error occurred while scrubbing metadata.", error_message, "SCR")
        self.scrub_button.setEnabled(True)

    def handle_file_drop(self, files):
        if files:
            file = files[0]
            if file.lower().endswith('.pdf'):
                self.selected_scrub_metadata_file = file
                filename = file.split('/')[-1].split('\\')[-1]
                self.scrub_metadata_file_label.setText(filename)
                self.preview.load_pdf(file)
