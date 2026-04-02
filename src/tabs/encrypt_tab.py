import random
import string
from PyQt6.QtWidgets import (
    QPushButton, QLabel, QLineEdit, QHBoxLayout, QMessageBox, QFileDialog, 
    QProgressDialog, QComboBox, QCheckBox, QProgressBar, QVBoxLayout, QWidget
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont

from widgets.feature_tab import FeatureTab, COLORS
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
        # Header
        header = self.create_header(
            "Encrypt PDF",
            "Protect your PDF with password encryption."
        )
        self.controls_layout.addWidget(header)
        
        # File selection
        self.file_container, self.file_label = self.create_file_label()
        self.controls_layout.addWidget(self.file_container)

        select_button = self.create_secondary_button("Select PDF", self.select_encrypt_file)
        self.controls_layout.addWidget(select_button)

        # Password Section
        pass_section, pass_layout = self.create_section("Password")
        
        self.password_input = self.create_password_input("Enter password")
        pass_layout.addWidget(self.password_input)
        
        self.confirm_password_input = self.create_password_input("Confirm password")
        pass_layout.addWidget(self.confirm_password_input)
        
        # Password options row
        options_row = QHBoxLayout()
        options_row.setSpacing(12)
        
        self.show_password = self.create_checkbox("Show")
        self.show_password.toggled.connect(self.toggle_password_visibility)
        options_row.addWidget(self.show_password)
        
        generate_btn = self.create_secondary_button("Generate", self.generate_and_set_password)
        generate_btn.setFixedWidth(100)
        options_row.addWidget(generate_btn)
        options_row.addStretch()
        
        pass_layout.addLayout(options_row)
        
        # Strength indicator
        strength_container = QWidget()
        strength_container.setStyleSheet("background: transparent;")
        strength_layout = QHBoxLayout(strength_container)
        strength_layout.setContentsMargins(0, 8, 0, 0)
        strength_layout.setSpacing(10)
        
        self.strength_bar = self.create_progress_bar()
        self.strength_bar.setRange(0, 4)
        self.strength_bar.setFixedWidth(120)
        strength_layout.addWidget(self.strength_bar)
        
        self.strength_label = QLabel("Weak")
        self.strength_label.setFont(QFont("Plus Jakarta Sans", 11))
        self.strength_label.setStyleSheet(f"color: {COLORS['error']}; background: transparent;")
        strength_layout.addWidget(self.strength_label)
        strength_layout.addStretch()
        
        self.password_input.textChanged.connect(self.update_password_strength)
        pass_layout.addWidget(strength_container)
        
        self.controls_layout.addWidget(pass_section)

        # Encryption Options Section
        options_section, options_layout = self.create_section("Encryption Options")
        
        # Encryption level
        level_row = QHBoxLayout()
        level_label = self.create_label("Encryption Level:")
        level_row.addWidget(level_label)
        
        self.encryption_level_input = self.create_dropdown(["128-bit AES", "256-bit AES"])
        self.encryption_level_input.setCurrentText("256-bit AES")
        level_row.addWidget(self.encryption_level_input, 1)
        options_layout.addLayout(level_row)
        
        self.controls_layout.addWidget(options_section)
        
        # Permissions Section
        perms_section, perms_layout = self.create_section("Permissions")
        
        self.print_checkbox = self.create_checkbox("Allow Printing", True)
        perms_layout.addWidget(self.print_checkbox)
        
        self.copy_checkbox = self.create_checkbox("Allow Copying", True)
        perms_layout.addWidget(self.copy_checkbox)
        
        self.modify_checkbox = self.create_checkbox("Allow Modifying", False)
        perms_layout.addWidget(self.modify_checkbox)
        
        self.controls_layout.addWidget(perms_section)

        # Action button
        self.encrypt_button = self.create_primary_button("Encrypt PDF", self.encrypt_file)
        self.controls_layout.addWidget(self.encrypt_button)
        
        self.controls_layout.addStretch()

    def toggle_password_visibility(self, show):
        mode = QLineEdit.EchoMode.Normal if show else QLineEdit.EchoMode.Password
        self.password_input.setEchoMode(mode)
        self.confirm_password_input.setEchoMode(mode)
        
    def generate_and_set_password(self):
        password = self.generate_password()
        self.password_input.setText(password)
        self.confirm_password_input.setText(password)
        
    def generate_password(self, length=16):
        chars = string.ascii_letters + string.digits + string.punctuation
        return "".join(random.choice(chars) for _ in range(length))

    def update_password_strength(self, password):
        strength = 0
        if any(c.islower() for c in password):
            strength += 1
        if any(c.isupper() for c in password):
            strength += 1
        if any(c.isdigit() for c in password):
            strength += 1
        if any(c in string.punctuation for c in password):
            strength += 1
        
        self.strength_bar.setValue(strength)
        
        if strength <= 1:
            color = COLORS['error']
            text = "Weak"
        elif strength <= 2:
            color = COLORS['warning']
            text = "Fair"
        elif strength <= 3:
            color = COLORS['warning']
            text = "Good"
        else:
            color = COLORS['success']
            text = "Strong"
            
        self.strength_label.setText(text)
        self.strength_label.setStyleSheet(f"color: {color}; background: transparent;")
        self.strength_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLORS['surface_elevated']};
                border: none;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 4px;
            }}
        """)

    def select_encrypt_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select PDF", "", "PDF Files (*.pdf)")
        if file:
            self.selected_encrypt_file = file
            filename = file.split('/')[-1].split('\\')[-1]
            self.file_label.setText(filename)
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
                filename = file.split('/')[-1].split('\\')[-1]
                self.file_label.setText(filename)
                self.preview.load_pdf(file)
