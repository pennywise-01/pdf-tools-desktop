from PyQt6.QtWidgets import (
    QPushButton, QLabel, QFileDialog, QMessageBox, QProgressDialog, QVBoxLayout
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont

from widgets.feature_tab import FeatureTab, COLORS
from features.pdf_to_word import convert_pdf_to_word

class PDFToWordWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, input_path, output_path):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path

    def run(self):
        try:
            success, msg = convert_pdf_to_word(self.input_path, self.output_path)
            if success:
                self.finished.emit(msg)
            else:
                self.error.emit(msg)
        except Exception as e:
            self.error.emit(str(e))

class PDFToWordTab(FeatureTab):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_file = None

    def setup_controls(self):
        # Header
        header = self.create_header(
            "PDF to Word",
            "Convert a PDF file into a Microsoft Word (.docx) document."
        )
        self.controls_layout.addWidget(header)

        # File selection
        self.file_container, self.file_label = self.create_file_label()
        self.controls_layout.addWidget(self.file_container)

        select_button = self.create_secondary_button("Select PDF", self.select_file)
        self.controls_layout.addWidget(select_button)

        # Action button
        self.action_button = self.create_primary_button("Convert to Word", self.run_action)
        self.controls_layout.addWidget(self.action_button)
        
        self.controls_layout.addStretch()

    def select_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select PDF", "", "PDF Files (*.pdf)")
        if file:
            self.selected_file = file
            filename = file.split('/')[-1].split('\\')[-1]
            self.file_label.setText(filename)
            self.preview.load_pdf(file)

    def run_action(self):
        if not self.selected_file:
            QMessageBox.warning(self, "No File Selected", "Please select a PDF file.")
            return

        output_path, _ = QFileDialog.getSaveFileName(self, "Save Word Document", "", "Word Documents (*.docx)")
        if output_path:
            self.progress_dialog = QProgressDialog("Converting to Word (this may take a while)...", "Cancel", 0, 0, self)
            self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            self.progress_dialog.show()

            self.worker = PDFToWordWorker(self.selected_file, output_path)
            self.worker.finished.connect(self.on_finished)
            self.worker.error.connect(self.on_error)
            self.worker.start()
            self.action_button.setEnabled(False)

    def on_finished(self, msg):
        self.progress_dialog.close()
        QMessageBox.information(self, "Success", msg)
        self.action_button.setEnabled(True)

    def on_error(self, error_message):
        self.progress_dialog.close()
        self.show_error("An error occurred.", error_message, "P2W")
        self.action_button.setEnabled(True)

    def handle_file_drop(self, files):
        if files:
            file = files[0]
            if file.lower().endswith('.pdf'):
                self.selected_file = file
                filename = file.split('/')[-1].split('\\')[-1]
                self.file_label.setText(filename)
                self.preview.load_pdf(file)
