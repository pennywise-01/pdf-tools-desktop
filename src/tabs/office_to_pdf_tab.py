from PyQt6.QtWidgets import (
    QPushButton, QLabel, QFileDialog, QMessageBox, QProgressDialog, QVBoxLayout
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont

from widgets.feature_tab import FeatureTab
from features.office_to_pdf import convert_office_to_pdf

class OfficeToPDFWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, input_path, output_path):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path

    def run(self):
        try:
            success, msg = convert_office_to_pdf(self.input_path, self.output_path)
            if success:
                self.finished.emit(msg)
            else:
                self.error.emit(msg)
        except Exception as e:
            self.error.emit(str(e))

class OfficeToPDFTab(FeatureTab):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_file = None

    def setup_controls(self):
        self.controls_layout.setSpacing(20)

        title = QLabel("Office to PDF")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        self.controls_layout.addWidget(title)
        
        description = QLabel("Convert Microsoft Office files (Word, Excel, PowerPoint) to PDF.")
        description.setWordWrap(True)
        description.setStyleSheet("color: #C0C0C0;")
        self.controls_layout.addWidget(description)

        self.file_label = QLabel("No file selected.")
        self.controls_layout.addWidget(self.file_label)

        select_button = QPushButton("Select Office File")
        select_button.clicked.connect(self.select_file)
        self.controls_layout.addWidget(select_button)

        self.action_button = QPushButton("Convert to PDF")
        self.action_button.clicked.connect(self.run_action)
        self.controls_layout.addWidget(self.action_button)
        
        self.controls_layout.addStretch()

    def select_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Office File", "", "Office Files (*.xlsx *.xls *.pptx *.ppt *.docx *.doc)")
        if file:
            self.selected_file = file
            self.file_label.setText(file)
            self.preview.clear()

    def run_action(self):
        if not self.selected_file:
            QMessageBox.warning(self, "No File Selected", "Please select a file first.")
            return

        output_path, _ = QFileDialog.getSaveFileName(self, "Save PDF", "", "PDF Files (*.pdf)")
        if output_path:
            self.progress_dialog = QProgressDialog("Converting to PDF...", "Cancel", 0, 0, self)
            self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            self.progress_dialog.show()

            self.worker = OfficeToPDFWorker(self.selected_file, output_path)
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
        self.show_error("An error occurred.", error_message, "O2P")
        self.action_button.setEnabled(True)

    def handle_file_drop(self, files):
        if files:
            file = files[0]
            ext = file.lower().split('.')[-1]
            if ext in ['xlsx', 'xls', 'pptx', 'ppt', 'docx', 'doc']:
                self.selected_file = file
                self.file_label.setText(file)
                self.preview.clear()
