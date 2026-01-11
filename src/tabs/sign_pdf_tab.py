from PyQt6.QtWidgets import (
    QPushButton, QMessageBox, QFileDialog, QProgressDialog,
    QVBoxLayout, QLabel, QLineEdit, QWidget, QHBoxLayout
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont

from widgets.feature_tab import FeatureTab
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
        # Title
        title = QLabel("Sign PDF")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        self.controls_layout.addWidget(title)

        description = QLabel("Digitally sign a PDF using a PFX/P12 certificate.")
        description.setWordWrap(True)
        self.controls_layout.addWidget(description)
        
        layout = QVBoxLayout()
        
        # Input PDF
        self.input_label = QLabel("No PDF selected")
        self.select_pdf_btn = QPushButton("Select PDF")
        self.select_pdf_btn.clicked.connect(self.select_pdf)
        
        # PFX File
        self.pfx_label = QLabel("No Certificate selected")
        self.select_pfx_btn = QPushButton("Select PFX/P12")
        self.select_pfx_btn.clicked.connect(self.select_pfx)
        
        # Password
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Certificate Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        # Sign Button
        self.sign_btn = QPushButton("Sign PDF")
        self.sign_btn.clicked.connect(self.sign_pdf)
        self.sign_btn.setEnabled(False)
        
        layout.addWidget(QLabel("1. Select PDF to Sign:"))
        layout.addWidget(self.input_label)
        layout.addWidget(self.select_pdf_btn)
        
        layout.addWidget(QLabel("2. Select Certificate:"))
        layout.addWidget(self.pfx_label)
        layout.addWidget(self.select_pfx_btn)
        
        layout.addWidget(QLabel("3. Enter Password:"))
        layout.addWidget(self.password_input)
        
        layout.addWidget(self.sign_btn)
        layout.addStretch()
        
        self.controls_layout.addLayout(layout)
        
    def select_pdf(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select PDF", "", "PDF Files (*.pdf)"
        )
        if path:
            self.input_path = path
            self.input_label.setText(path)
            self.check_ready()
            
    def select_pfx(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Certificate", "", "PFX/P12 Files (*.pfx *.p12)"
        )
        if path:
            self.pfx_path = path
            self.pfx_label.setText(path)
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
