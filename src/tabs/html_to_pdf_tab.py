from PyQt6.QtWidgets import (
    QPushButton, QMessageBox, QFileDialog, QProgressDialog,
    QVBoxLayout, QLabel, QLineEdit, QWidget
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont

from widgets.feature_tab import FeatureTab, COLORS
from features.html_to_pdf import convert_html_to_pdf, is_wkhtmltopdf_installed, install_wkhtmltopdf_help

class HtmlToPdfWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, source, output_path):
        super().__init__()
        self.source = source
        self.output_path = output_path

    def run(self):
        try:
            convert_html_to_pdf(self.source, self.output_path)
            self.finished.emit(self.output_path)
        except Exception as e:
            self.error.emit(str(e))

class HtmlToPdfTab(FeatureTab):
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def setup_controls(self):
        # Header
        header = self.create_header(
            "HTML to PDF",
            "Enter a URL or select an HTML file to convert to a PDF."
        )
        self.controls_layout.addWidget(header)

        # URL input
        self.url_input = self.create_input("Enter URL here")
        self.controls_layout.addWidget(self.url_input)

        # Buttons
        select_button = self.create_secondary_button("Select HTML File", self.select_html_file)
        self.controls_layout.addWidget(select_button)

        self.convert_button = self.create_primary_button("Convert to PDF", self.convert)
        self.controls_layout.addWidget(self.convert_button)
        
        self.controls_layout.addStretch()

    def select_html_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select HTML File", "", "HTML Files (*.html *.htm)")
        if file:
            self.url_input.setText(file)

    def convert(self):
        # Check dependency first
        if not is_wkhtmltopdf_installed():
            reply = QMessageBox.question(
                self, 
                "Missing Dependency", 
                "This feature requires 'wkhtmltopdf' to be installed.\n\n"
                "Would you like to open the download page to install it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                install_wkhtmltopdf_help()
            return

        source = self.url_input.text()
        if not source:
            QMessageBox.warning(self, "No Source", "Please enter a URL or select an HTML file.")
            return

        output_path, _ = QFileDialog.getSaveFileName(self, "Save PDF", "", "PDF Files (*.pdf)")
        if output_path:
            self.progress_dialog = QProgressDialog("Converting HTML to PDF...", "Cancel", 0, 0, self)
            self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            self.progress_dialog.show()

            self.worker = HtmlToPdfWorker(source, output_path)
            self.worker.finished.connect(self.on_conversion_finished)
            self.worker.error.connect(self.on_conversion_error)
            self.worker.start()
            self.convert_button.setEnabled(False)

    def on_conversion_finished(self, output_path):
        self.progress_dialog.close()
        QMessageBox.information(self, "Success", f"Successfully converted to {output_path}")
        self.url_input.clear()
        self.convert_button.setEnabled(True)

    def on_conversion_error(self, error_message):
        self.progress_dialog.close()
        self.show_error("An error occurred during conversion.", error_message, "HTM")
        self.convert_button.setEnabled(True)
