from PyQt6.QtWidgets import (
    QPushButton, QLabel, QHBoxLayout, QMessageBox, QFileDialog, 
    QProgressDialog, QVBoxLayout, QLineEdit, QCheckBox, QComboBox, QWidget
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont

from widgets.feature_tab import FeatureTab, COLORS
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
        # Header
        header = self.create_header(
            "Redact PDF",
            "Permanently remove sensitive text from your PDF."
        )
        self.controls_layout.addWidget(header)

        # File selection
        self.file_container, self.file_label = self.create_file_label()
        self.controls_layout.addWidget(self.file_container)

        select_button = self.create_secondary_button("Select PDF", self.select_file)
        self.controls_layout.addWidget(select_button)

        # Redaction settings section
        redaction_section, redaction_layout = self.create_section("Redaction Settings")
        
        # Text input
        input_label = self.create_label("Terms to redact (comma separated):")
        redaction_layout.addWidget(input_label)
        
        self.text_input = self.create_input("Enter terms, e.g., Secret, ID, SSN")
        redaction_layout.addWidget(self.text_input)
        
        # Options
        self.match_case_check = self.create_checkbox("Match Case")
        redaction_layout.addWidget(self.match_case_check)
        
        self.redact_numbers_check = self.create_checkbox("Redact All Numbers/Digits")
        redaction_layout.addWidget(self.redact_numbers_check)
        
        # Color Selection
        color_layout = QHBoxLayout()
        color_label = self.create_label("Redaction Color:")
        color_layout.addWidget(color_label)
        self.color_combo = self.create_dropdown(["Black", "White", "Red"])
        self.color_combo.setItemData(0, (0, 0, 0))
        self.color_combo.setItemData(1, (1, 1, 1))
        self.color_combo.setItemData(2, (1, 0, 0))
        color_layout.addWidget(self.color_combo)
        color_layout.addStretch()
        redaction_layout.addLayout(color_layout)
        
        self.controls_layout.addWidget(redaction_section)

        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)
        
        self.preview_button = self.create_secondary_button("Preview Redactions", self.preview_redaction)
        buttons_layout.addWidget(self.preview_button)

        self.redact_button = self.create_danger_button("Apply Redaction", self.redact_file)
        buttons_layout.addWidget(self.redact_button)
        
        self.controls_layout.addLayout(buttons_layout)
        
        self.controls_layout.addStretch()

    def select_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select PDF", "", "PDF Files (*.pdf)")
        if file:
            self.selected_file = file
            filename = file.split('/')[-1].split('\\')[-1]
            self.file_label.setText(filename)
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
                filename = file.split('/')[-1].split('\\')[-1]
                self.file_label.setText(filename)
                self.preview.load_pdf(file)
