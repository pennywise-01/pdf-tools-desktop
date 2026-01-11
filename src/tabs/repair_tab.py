from PyQt6.QtWidgets import (
    QPushButton, QLabel, QMessageBox, QFileDialog, QProgressDialog
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont

from widgets.feature_tab import FeatureTab
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
        self.controls_layout.setSpacing(20)

        title = QLabel("Repair PDF")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        self.controls_layout.addWidget(title)

        description = QLabel("Fix corrupted PDF files by rebuilding the XREF table.")
        description.setWordWrap(True)
        description.setStyleSheet("color: #C0C0C0;")
        self.controls_layout.addWidget(description)

        self.file_label = QLabel("No file selected.")
        self.controls_layout.addWidget(self.file_label)

        select_button = QPushButton("Select Corrupted PDF")
        select_button.clicked.connect(self.select_file)
        self.controls_layout.addWidget(select_button)

        self.repair_button = QPushButton("Repair PDF")
        self.repair_button.setObjectName("action_button")
        self.repair_button.clicked.connect(self.repair_file)
        self.controls_layout.addWidget(self.repair_button)
        
        self.controls_layout.addStretch()

    def select_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select PDF", "", "PDF Files (*.pdf)")
        if file:
            self.selected_file = file
            self.file_label.setText(file)
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
