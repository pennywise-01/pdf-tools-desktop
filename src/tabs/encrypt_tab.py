import random
import string
from PyQt6.QtWidgets import (
    QPushButton, QLabel, QLineEdit, QHBoxLayout, QMessageBox, QFileDialog, 
    QProgressDialog, QComboBox, QCheckBox, QProgressBar, QVBoxLayout, QWidget
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont

from widgets.feature_tab import FeatureTab
from features.encrypt_pdf import encrypt_pdf

class EncryptWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, input_path, output_path, password, permissions, encryption_level):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.password = password
        self.permissions = permissions
        self.encryption_level = encryption_level

    def run(self):
        try:
            encrypt_pdf(self.input_path, self.output_path, self.password, self.permissions, self.encryption_level)
            self.finished.emit(self.output_path)
        except Exception as e:
            self.error.emit(str(e))

class EncryptTab(FeatureTab):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_encrypt_file = None

    def setup_controls(self):
        self.controls_layout.setSpacing(20)

        title = QLabel("Encrypt PDF")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        self.controls_layout.addWidget(title)

        description = QLabel("Select a PDF file and add a password to protect it.")
        description.setWordWrap(True)
        description.setStyleSheet("color: #C0C0C0;")
        self.controls_layout.addWidget(description)
        
        self.encrypt_file_label = QLabel("No file selected.")
        self.controls_layout.addWidget(self.encrypt_file_label)

        select_button = QPushButton("Select PDF")
        select_button.clicked.connect(self.select_encrypt_file)
        self.controls_layout.addWidget(select_button)

        # Password
        self.password_input, self.confirm_password_input = self.create_password_field("Password:")
        
        # Encryption Level
        encryption_layout = QHBoxLayout()
        encryption_label = QLabel("Encryption Level:")
        encryption_layout.addWidget(encryption_label)
        self.encryption_level_input = QComboBox()
        self.encryption_level_input.addItems(["128-bit AES", "256-bit AES"])
        self.encryption_level_input.setCurrentText("256-bit AES")
        encryption_layout.addWidget(self.encryption_level_input)
        self.controls_layout.addLayout(encryption_layout)
        
        # Permissions
        permissions_label = QLabel("Permissions:")
        self.controls_layout.addWidget(permissions_label)
        self.print_checkbox = QCheckBox("Allow Printing")
        self.print_checkbox.setChecked(True)
        self.controls_layout.addWidget(self.print_checkbox)
        self.copy_checkbox = QCheckBox("Allow Copying")
        self.copy_checkbox.setChecked(True)
        self.controls_layout.addWidget(self.copy_checkbox)
        self.modify_checkbox = QCheckBox("Allow Modifying")
        self.modify_checkbox.setChecked(False)
        self.controls_layout.addWidget(self.modify_checkbox)

        self.encrypt_button = QPushButton("Encrypt PDF")
        self.encrypt_button.setObjectName("encrypt_button")
        self.encrypt_button.clicked.connect(self.encrypt_file)
        self.controls_layout.addWidget(self.encrypt_button)
        
        self.controls_layout.addStretch()

    def create_password_field(self, label):
        layout = QVBoxLayout()
        
        pass_layout = QHBoxLayout()
        pass_label = QLabel(label)
        pass_layout.addWidget(pass_label)
        password_input = QLineEdit()
        password_input.setEchoMode(QLineEdit.EchoMode.Password)
        pass_layout.addWidget(password_input)
        layout.addLayout(pass_layout)

        confirm_pass_layout = QHBoxLayout()
        confirm_pass_label = QLabel("Confirm " + label)
        confirm_pass_layout.addWidget(confirm_pass_label)
        confirm_password_input = QLineEdit()
        confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        confirm_pass_layout.addWidget(confirm_password_input)
        layout.addLayout(confirm_pass_layout)

        buttons_layout = QHBoxLayout()
        show_hide_button = QCheckBox("Show")
        show_hide_button.toggled.connect(lambda checked: password_input.setEchoMode(QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password))
        show_hide_button.toggled.connect(lambda checked: confirm_password_input.setEchoMode(QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password))
        buttons_layout.addWidget(show_hide_button)

        generate_button = QPushButton("Generate")
        generate_button.clicked.connect(lambda: self.set_generated_password(password_input, confirm_password_input))
        buttons_layout.addWidget(generate_button)
        layout.addLayout(buttons_layout)

        strength_layout = QHBoxLayout()
        strength_bar = QProgressBar()
        strength_bar.setRange(0, 4)
        strength_bar.setTextVisible(False)
        strength_layout.addWidget(strength_bar)
        
        strength_label = QLabel("Weak")
        strength_layout.addWidget(strength_label)
        
        password_input.textChanged.connect(lambda text: self.update_password_strength(text, strength_bar, strength_label))
        layout.addLayout(strength_layout)
        
        self.controls_layout.addLayout(layout)
        return password_input, confirm_password_input
    
    def set_generated_password(self, password_input, confirm_password_input):
        password = self.generate_password()
        password_input.setText(password)
        confirm_password_input.setText(password)
        
    def generate_password(self, length=16):
        chars = string.ascii_letters + string.digits + string.punctuation
        return "".join(random.choice(chars) for _ in range(length))

    def update_password_strength(self, password, strength_bar, strength_label):
        strength = 0
        if any(c.islower() for c in password):
            strength += 1
        if any(c.isupper() for c in password):
            strength += 1
        if any(c.isdigit() for c in password):
            strength += 1
        if any(c in string.punctuation for c in password):
            strength += 1
        
        strength_bar.setValue(strength)
        if strength <= 1:
            strength_bar.setStyleSheet("QProgressBar::chunk { background-color: #E94560; }")
            strength_label.setText("Weak")
        elif strength <= 3:
            strength_bar.setStyleSheet("QProgressBar::chunk { background-color: orange; }")
            strength_label.setText("Medium")
        else:
            strength_bar.setStyleSheet("QProgressBar::chunk { background-color: lightgreen; }")
            strength_label.setText("Strong")

    def select_encrypt_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select PDF", "", "PDF Files (*.pdf)")
        if file:
            self.selected_encrypt_file = file
            self.encrypt_file_label.setText(file)
            self.preview.load_pdf(file)

    def encrypt_file(self):
        if not self.selected_encrypt_file:
            QMessageBox.warning(self, "No File Selected", "Please select a PDF file to encrypt.")
            return

        password = self.password_input.text()
        if password != self.confirm_password_input.text():
            QMessageBox.warning(self, "Passwords Do Not Match", "Passwords do not match.")
            return

        if not password:
            QMessageBox.warning(self, "Password Required", "Please enter a password.")
            return

        permissions = {
            'print': self.print_checkbox.isChecked(),
            'copy': self.copy_checkbox.isChecked(),
            'modify': self.modify_checkbox.isChecked()
        }
        
        encryption_level = 256 if self.encryption_level_input.currentText() == "256-bit AES" else 128

        output_path, _ = QFileDialog.getSaveFileName(self, "Save Encrypted PDF", "", "PDF Files (*.pdf)")
        if output_path:
            self.progress_dialog = QProgressDialog("Encrypting PDF...", "Cancel", 0, 0, self)
            self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            self.progress_dialog.show()

            self.worker = EncryptWorker(self.selected_encrypt_file, output_path, password, permissions, encryption_level)
            self.worker.finished.connect(self.on_encrypt_finished)
            self.worker.error.connect(self.on_encrypt_error)
            self.worker.start()
            self.encrypt_button.setEnabled(False)

    def on_encrypt_finished(self, output_path):
        self.progress_dialog.close()
        QMessageBox.information(self, "Success", f"Successfully encrypted and saved PDF to {output_path}")
        self.preview.clear()
        self.encrypt_file_label.setText("No file selected.")
        self.selected_encrypt_file = None
        self.password_input.clear()
        self.confirm_password_input.clear()
        self.encrypt_button.setEnabled(True)

    def on_encrypt_error(self, error_message):
        self.progress_dialog.close()
        self.show_error("An error occurred while encrypting the PDF.", error_message, "ENC")
        self.encrypt_button.setEnabled(True)

    def handle_file_drop(self, files):
        if files:
            file = files[0]
            if file.lower().endswith('.pdf'):
                self.selected_encrypt_file = file
                self.encrypt_file_label.setText(file)
                self.preview.load_pdf(file)
