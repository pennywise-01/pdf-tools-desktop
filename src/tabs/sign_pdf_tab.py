from PyQt6.QtWidgets import (
    QPushButton, QMessageBox, QFileDialog, QProgressDialog,
    QVBoxLayout, QLabel, QLineEdit, QWidget, QHBoxLayout
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont

from widgets.feature_tab import FeatureTab, COLORS
from features.sign_pdf import sign_pdf

class SignPdfWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, input_path, output_path, pfx_path, password):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.pfx_path = pfx_path
        self.password = password

    def run(self):
        try:
            sign_pdf(self.input_path, self.output_path, self.pfx_path, self.password)
            self.finished.emit(self.output_path)
        except Exception as e:
            self.error.emit(str(e))

class SignPdfTab(FeatureTab):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.input_path = None
        self.pfx_path = None
        
    def setup_controls(self):
        # Header
        header = self.create_header(
            "Sign PDF",
            "Digitally sign a PDF using a PFX/P12 certificate."
        )
        self.controls_layout.addWidget(header)
        
        # Step 1: PDF selection
        step1_label = self.create_label("1. Select PDF to Sign:")
        self.controls_layout.addWidget(step1_label)
        
        self.pdf_container, self.input_label = self.create_file_label("No PDF selected")
        self.controls_layout.addWidget(self.pdf_container)
        
        self.select_pdf_btn = self.create_secondary_button("Select PDF", self.select_pdf)
        self.controls_layout.addWidget(self.select_pdf_btn)
        
        # Step 2: Certificate selection
        step2_label = self.create_label("2. Select Certificate:")
        self.controls_layout.addWidget(step2_label)
        
        self.pfx_container, self.pfx_label = self.create_file_label("No Certificate selected")
        self.controls_layout.addWidget(self.pfx_container)
        
        self.select_pfx_btn = self.create_secondary_button("Select PFX/P12", self.select_pfx)
        self.controls_layout.addWidget(self.select_pfx_btn)
        
        # Step 3: Password
        step3_label = self.create_label("3. Enter Password:")
        self.controls_layout.addWidget(step3_label)
        
        self.password_input = self.create_password_input("Certificate Password")
        self.controls_layout.addWidget(self.password_input)
        
        # Sign Button
        self.sign_btn = self.create_primary_button("Sign PDF", self.sign_pdf)
        self.sign_btn.setEnabled(False)
        self.controls_layout.addWidget(self.sign_btn)
        
        self.controls_layout.addStretch()
        
    def select_pdf(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select PDF", "", "PDF Files (*.pdf)"
        )
        if path:
            self.input_path = path
            filename = path.split('/')[-1].split('\\')[-1]
            self.input_label.setText(filename)
            self.check_ready()
            
    def select_pfx(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Certificate", "", "PFX/P12 Files (*.pfx *.p12)"
        )
        if path:
            self.pfx_path = path
            filename = path.split('/')[-1].split('\\')[-1]
            self.pfx_label.setText(filename)
            self.check_ready()
            
    def check_ready(self):
        self.sign_btn.setEnabled(bool(self.input_path and self.pfx_path))
        
    def sign_pdf(self):
        output_path, _ = QFileDialog.getSaveFileName(
            self, "Save Signed PDF", "", "PDF Files (*.pdf)"
        )
        
        if not output_path:
            return
            
        password = self.password_input.text()
        
        self.worker = SignPdfWorker(self.input_path, output_path, self.pfx_path, password)
        self.worker.finished.connect(self.on_success)
        self.worker.error.connect(self.on_error)
        
        self.progress = QProgressDialog("Signing PDF...", "Cancel", 0, 0, self)
        self.progress.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress.show()
        
        self.worker.start()
        
    def on_success(self, output_path):
        self.progress.close()
        QMessageBox.information(self, "Success", f"PDF signed successfully!\nSaved to: {output_path}")
        self.input_path = None
        self.pfx_path = None
        self.input_label.setText("No PDF selected")
        self.pfx_label.setText("No Certificate selected")
        self.password_input.clear()
        self.check_ready()
        
    def on_error(self, error_msg):
        self.progress.close()
        self.show_error("Failed to sign PDF.", error_msg, "SGN")
