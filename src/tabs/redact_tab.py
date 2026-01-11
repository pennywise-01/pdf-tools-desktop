from PyQt6.QtWidgets import (
    QPushButton, QLabel, QHBoxLayout, QMessageBox, QFileDialog, 
    QProgressDialog, QVBoxLayout, QLineEdit, QCheckBox, QComboBox, QWidget
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont

from widgets.feature_tab import FeatureTab
from features.redact_pdf import redact_pdf

import os

class RedactWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, input_path, output_path, text, match_case, redact_numbers, color, preview_mode=False):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.text = text
        self.match_case = match_case
        self.redact_numbers = redact_numbers
        self.color = color
        self.preview_mode = preview_mode

    def run(self):
        try:
            redact_pdf(
                self.input_path, 
                self.output_path, 
                self.text,
                match_case=self.match_case,
                redact_numbers=self.redact_numbers,
                color=self.color,
                preview_mode=self.preview_mode
            )
            self.finished.emit(self.output_path)
        except Exception as e:
            self.error.emit(str(e))

class RedactTab(FeatureTab):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_file = None

    def setup_controls(self):
        self.controls_layout.setSpacing(15)

        title = QLabel("Redact PDF")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        self.controls_layout.addWidget(title)
        
        description = QLabel("Permanently remove sensitive text from your PDF.")
        description.setWordWrap(True)
        description.setStyleSheet("color: #C0C0C0;")
        self.controls_layout.addWidget(description)

        self.file_label = QLabel("No file selected.")
        self.controls_layout.addWidget(self.file_label)

        select_button = QPushButton("Select PDF")
        select_button.clicked.connect(self.select_file)
        self.controls_layout.addWidget(select_button)

        # Redaction Input
        input_label = QLabel("Redactions:")
        self.controls_layout.addWidget(input_label)
        
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Enter terms, csv (e.g., Secret, ID)")
        self.controls_layout.addWidget(self.text_input)
        
        # Options Group
        options_layout = QVBoxLayout()
        options_layout.setSpacing(5)
        
        self.match_case_check = QCheckBox("Match Case")
        options_layout.addWidget(self.match_case_check)
        
        self.redact_numbers_check = QCheckBox("Redact All Numbers/Digits")
        self.redact_numbers_check.setToolTip("Redacts any words containing digits (e.g. 12345, ID-99)")
        options_layout.addWidget(self.redact_numbers_check)
        
        self.controls_layout.addLayout(options_layout)
        
        # Color Selection
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Color:"))
        self.color_combo = QComboBox()
        self.color_combo.addItem("Black", (0, 0, 0))
        self.color_combo.addItem("White", (1, 1, 1))
        self.color_combo.addItem("Red", (1, 0, 0))
        color_layout.addWidget(self.color_combo)
        self.controls_layout.addLayout(color_layout)

        # Buttons
        button_layout = QHBoxLayout()
        
        self.preview_button = QPushButton("Preview Redactions")
        self.preview_button.clicked.connect(self.preview_redaction)
        self.preview_button.setStyleSheet("background-color: #555555; color: white;")
        button_layout.addWidget(self.preview_button)

        self.redact_button = QPushButton("Apply Redaction")
        self.redact_button.setObjectName("redact_button")
        self.redact_button.clicked.connect(self.redact_file)
        # Make apply button prominent - usually reddish for destructive action
        self.redact_button.setStyleSheet("background-color: darkred; color: white; font-weight: bold;")
        button_layout.addWidget(self.redact_button)
        
        self.controls_layout.addLayout(button_layout)
        
        self.controls_layout.addStretch()

    def select_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select PDF", "", "PDF Files (*.pdf)")
        if file:
            self.selected_file = file
            self.file_label.setText(file)
            self.preview.load_pdf(file)

    def get_options(self):
        text = self.text_input.text().strip()
        match_case = self.match_case_check.isChecked()
        redact_numbers = self.redact_numbers_check.isChecked()
        color = self.color_combo.currentData()
        return text, match_case, redact_numbers, color

    def preview_redaction(self):
        if not self.selected_file:
            QMessageBox.warning(self, "No File Selected", "Please select a PDF file.")
            return

        text, match_case, redact_numbers, color = self.get_options()
        
        if not text and not redact_numbers:
            QMessageBox.warning(self, "No Criteria", "Please enter text or select 'Redact Numbers'.")
            return
            
        # Create a temp file for preview
        import tempfile
        temp_dir = tempfile.gettempdir()
        preview_path = os.path.join(temp_dir, "preview_redaction.pdf")
        
        self.progress_dialog = QProgressDialog("Generating Preview...", "Cancel", 0, 0, self)
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.show()
        
        self.worker = RedactWorker(
            self.selected_file, 
            preview_path, 
            text, 
            match_case, 
            redact_numbers, 
            color, 
            preview_mode=True
        )
        self.worker.finished.connect(self.on_preview_finished)
        self.worker.error.connect(self.on_error)
        self.worker.start()
        self.preview_button.setEnabled(False)

    def on_preview_finished(self, output_path):
        self.progress_dialog.close()
        # Load the preview PDF (with highlights) into the viewer
        self.preview.load_pdf(output_path)
        self.preview_button.setEnabled(True)
        QMessageBox.information(self, "Preview Ready", "Terms to be redacted are highlighted in YELLOW.\n\nNote: This is just a preview. Redaction is permanent when you click 'Apply'.")

    def redact_file(self):
        if not self.selected_file:
            QMessageBox.warning(self, "No File Selected", "Please select a PDF file.")
            return
            
        text, match_case, redact_numbers, color = self.get_options()
        
        if not text and not redact_numbers:
            QMessageBox.warning(self, "No Criteria", "Please enter text or select 'Redact Numbers'.")
            return

        output_path, _ = QFileDialog.getSaveFileName(self, "Save Redacted PDF", "", "PDF Files (*.pdf)")
        if output_path:
            self.progress_dialog = QProgressDialog("Permanently Redacting...", "Cancel", 0, 0, self)
            self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            self.progress_dialog.show()

            self.worker = RedactWorker(
                self.selected_file, 
                output_path, 
                text, 
                match_case, 
                redact_numbers, 
                color, 
                preview_mode=False
            )
            self.worker.finished.connect(self.on_finished)
            self.worker.error.connect(self.on_error)
            self.worker.start()
            self.redact_button.setEnabled(False)

    def on_finished(self, output_path):
        self.progress_dialog.close()
        QMessageBox.information(self, "Success", f"PDF redacted successfully to {output_path}")
        # Could reload the result, but usually safer to clear or keep original
        # Let's clear preview to show job done
        self.preview.clear() 
        self.file_label.setText("No file selected.")
        self.selected_file = None
        self.redact_button.setEnabled(True)
        self.text_input.clear()
        self.match_case_check.setChecked(False)
        self.redact_numbers_check.setChecked(False)

    def on_error(self, error_message):
        self.progress_dialog.close()
        self.show_error("An error occurred while redacting the PDF.", error_message, "RED")
        self.redact_button.setEnabled(True)
        self.preview_button.setEnabled(True)

    def handle_file_drop(self, files):
        if files:
            file = files[0]
            if file.lower().endswith('.pdf'):
                self.selected_file = file
                self.file_label.setText(file)
                self.preview.load_pdf(file)
