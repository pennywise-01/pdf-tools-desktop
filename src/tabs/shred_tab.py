from PyQt6.QtWidgets import (
    QPushButton, QLabel, QHBoxLayout, QMessageBox, QFileDialog, 
    QProgressDialog, QVBoxLayout
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont

from widgets.feature_tab import FeatureTab, COLORS
from features.shred_file import shred_file

class ShredWorker(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    def run(self):
        try:
            shred_file(self.file_path)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

class ShredTab(FeatureTab):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_file = None

    def setup_controls(self):
        # Header with warning styling
        header = self.create_header(
            "Secure Shred",
            "Safely and permanently destroy files using DoD 5220.22-M standards. Files shredded here CANNOT be recovered."
        )
        self.controls_layout.addWidget(header)

        # File selection
        self.file_container, self.file_label = self.create_file_label()
        self.controls_layout.addWidget(self.file_container)

        select_button = self.create_secondary_button("Select File to Destroy", self.select_file)
        self.controls_layout.addWidget(select_button)

        # Warning info
        warning_label = self.create_info_label("⚠️ This action is permanent and cannot be undone.")
        self.controls_layout.addWidget(warning_label)

        # Action button - danger styling
        self.shred_button = self.create_danger_button("SHRED FILE FOREVER", self.shred_file)
        self.controls_layout.addWidget(self.shred_button)
        
        self.controls_layout.addStretch()

    def select_file(self):
        # Allow any file, but default to PDF
        file, _ = QFileDialog.getOpenFileName(self, "Select Any File", "", "All Files (*.*);;PDF Files (*.pdf)")
        if file:
            self.selected_file = file
            filename = file.split('/')[-1].split('\\')[-1]
            self.file_label.setText(filename)
            if file.lower().endswith('.pdf'):
                self.preview.load_pdf(file)
            else:
                self.preview.clear()

    def shred_file(self):
        if not self.selected_file:
            QMessageBox.warning(self, "No File Selected", "Please select a file to shred.")
            return

        confirm = QMessageBox.question(
            self, 
            "PERMANENT DELETION WARNING", 
            f"Are you absolutely sure you want to securely destroy:\n\n{self.selected_file}\n\nThis action CANNOT be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            # Clear preview to release file handle
            self.preview.clear()
            
            self.progress_dialog = QProgressDialog("Shredding File...", None, 0, 0, self)
            self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            self.progress_dialog.setCancelButton(None) # Cannot cancel shredding once started logic-wise, safer to block
            self.progress_dialog.show()

            self.worker = ShredWorker(self.selected_file)
            self.worker.finished.connect(self.on_finished)
            self.worker.error.connect(self.on_error)
            self.worker.start()
            self.shred_button.setEnabled(False)

    def on_finished(self):
        self.progress_dialog.close()
        QMessageBox.information(self, "Shredded", "File has been securely destroyed.")
        self.file_label.setText("No file selected.")
        self.selected_file = None
        self.shred_button.setEnabled(True)

    def on_error(self, error_message):
        self.progress_dialog.close()
        self.show_error("An error occurred while shredding the file.", error_message, "SHR")
        self.shred_button.setEnabled(True)

    def handle_file_drop(self, files):
        if files:
            file = files[0]
            self.selected_file = file
            filename = file.split('/')[-1].split('\\')[-1]
            self.file_label.setText(filename)
            if file.lower().endswith('.pdf'):
                self.preview.load_pdf(file)
            else:
                self.preview.clear()
