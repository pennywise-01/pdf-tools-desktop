from PyQt6.QtWidgets import (
    QPushButton, QLabel, QMessageBox, QFileDialog, QProgressDialog
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont

from widgets.feature_tab import FeatureTab, COLORS
from features.repair_pdf import repair_pdf

class RepairWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, input_path, output_path):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path

    def run(self):
        try:
            success = repair_pdf(self.input_path, self.output_path)
            if success:
                self.finished.emit(self.output_path)
            else:
                self.error.emit("Repair process returned False.")
        except Exception as e:
            self.error.emit(str(e))

class RepairTab(FeatureTab):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_file = None

    def setup_controls(self):
        # Header
        header = self.create_header(
            "Repair PDF",
            "Fix corrupted PDF files by rebuilding the XREF table."
        )
        self.controls_layout.addWidget(header)

        # File selection
        self.file_container, self.file_label = self.create_file_label()
        self.controls_layout.addWidget(self.file_container)

        select_button = self.create_secondary_button("Select Corrupted PDF", self.select_file)
        self.controls_layout.addWidget(select_button)

        # Action button
        self.repair_button = self.create_primary_button("Repair PDF", self.repair_file)
        self.controls_layout.addWidget(self.repair_button)
        
        self.controls_layout.addStretch()

    def select_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select PDF", "", "PDF Files (*.pdf)")
        if file:
            self.selected_file = file
            filename = file.split('/')[-1].split('\\')[-1]
            self.file_label.setText(filename)
            self.preview.load_pdf(file)

    def repair_file(self):
        if not self.selected_file:
            QMessageBox.warning(self, "No File Selected", "Please select a PDF file.")
            return

        save_path, _ = QFileDialog.getSaveFileName(self, "Save Repaired PDF", "", "PDF Files (*.pdf)")
        if not save_path:
            return

        self.progress = QProgressDialog("Repairing PDF...", "Cancel", 0, 0, self)
        self.progress.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress.show()

        self.worker = RepairWorker(self.selected_file, save_path)
        self.worker.finished.connect(self.on_repair_finished)
        self.worker.error.connect(self.on_repair_error)
        self.worker.start()

    def on_repair_finished(self, output_path):
        self.progress.cancel()
        QMessageBox.information(self, "Success", f"PDF repaired and saved to:\n{output_path}")

    def on_repair_error(self, error_msg):
        self.progress.cancel()
        QMessageBox.critical(self, "Error", f"Failed to repair PDF:\n{error_msg}")
