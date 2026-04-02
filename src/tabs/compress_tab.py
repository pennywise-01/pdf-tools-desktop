from PyQt6.QtWidgets import (
    QPushButton, QLabel, QHBoxLayout, QMessageBox, QFileDialog, 
    QProgressDialog, QVBoxLayout, QSlider, QFrame
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont

from widgets.feature_tab import FeatureTab, COLORS
from features.compress_pdf import compress_pdf


class CompressWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, input_path, output_path, quality):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.quality = quality

    def run(self):
        try:
            compress_pdf(self.input_path, self.output_path, self.quality)
            self.finished.emit(self.output_path)
        except Exception as e:
            self.error.emit(str(e))


class CompressTab(FeatureTab):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_file = None

    def setup_controls(self):
        # Header
        header = self.create_header(
            "Compress PDF",
            "Reduce the file size of your PDF while maintaining quality."
        )
        self.controls_layout.addWidget(header)

        # File selection
        self.file_container, self.file_label = self.create_file_label()
        self.controls_layout.addWidget(self.file_container)

        select_button = self.create_secondary_button("Select PDF", self.select_file)
        self.controls_layout.addWidget(select_button)

        # Compression Level Section
        level_section, level_layout = self.create_section("Compression Level")
        
        self.level_slider = self.create_slider(0, 4, 4)
        self.level_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.level_slider.setTickInterval(1)
        self.level_slider.valueChanged.connect(self.update_level_label)
        level_layout.addWidget(self.level_slider)
        
        # Level indicator
        level_indicator = QHBoxLayout()
        level_indicator.setContentsMargins(0, 8, 0, 0)
        
        self.level_label = QLabel("Maximum")
        self.level_label.setFont(QFont("Plus Jakarta Sans", 13, QFont.Weight.DemiBold))
        self.level_label.setStyleSheet(f"color: {COLORS['accent']}; background: transparent;")
        level_indicator.addWidget(self.level_label)
        
        self.level_desc = QLabel("Best compression, smallest file size")
        self.level_desc.setFont(QFont("Plus Jakarta Sans", 11))
        self.level_desc.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        level_indicator.addWidget(self.level_desc)
        level_indicator.addStretch()
        
        level_layout.addLayout(level_indicator)
        self.controls_layout.addWidget(level_section)

        # Action button
        self.compress_button = self.create_primary_button("Compress PDF", self.compress_file)
        self.controls_layout.addWidget(self.compress_button)
        
        self.controls_layout.addStretch()

    def update_level_label(self, value):
        labels = {
            0: ("None", "Just copy, no compression"),
            1: ("Low", "Clean objects only"),
            2: ("Medium", "Deflate streams"),
            3: ("High", "Deduplicate resources"),
            4: ("Maximum", "Best compression, smallest file size")
        }
        name, desc = labels.get(value, ("Unknown", ""))
        self.level_label.setText(name)
        self.level_desc.setText(desc)

    def select_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select PDF", "", "PDF Files (*.pdf)")
        if file:
            self.selected_file = file
            filename = file.split('/')[-1].split('\\')[-1]
            self.file_label.setText(filename)
            self.preview.load_pdf(file)

    def compress_file(self):
        if not self.selected_file:
            QMessageBox.warning(self, "No File Selected", "Please select a PDF file.")
            return

        quality = self.level_slider.value()

        output_path, _ = QFileDialog.getSaveFileName(self, "Save Compressed PDF", "", "PDF Files (*.pdf)")
        if output_path:
            self.progress_dialog = QProgressDialog("Compressing PDF...", "Cancel", 0, 0, self)
            self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            self.progress_dialog.show()

            self.worker = CompressWorker(self.selected_file, output_path, quality)
            self.worker.finished.connect(self.on_finished)
            self.worker.error.connect(self.on_error)
            self.worker.start()
            self.compress_button.setEnabled(False)

    def on_finished(self, output_path):
        self.progress_dialog.close()
        QMessageBox.information(self, "Success", f"PDF compressed successfully to {output_path}")
        self.preview.clear()
        self.file_label.setText("No file selected.")
        self.selected_file = None
        self.compress_button.setEnabled(True)

    def on_error(self, error_message):
        self.progress_dialog.close()
        self.show_error("An error occurred while compressing the PDF.", error_message, "CMP")
        self.compress_button.setEnabled(True)

    def handle_file_drop(self, files):
        if files:
            file = files[0]
            if file.lower().endswith('.pdf'):
                self.selected_file = file
                filename = file.split('/')[-1].split('\\')[-1]
                self.file_label.setText(filename)
                self.preview.load_pdf(file)
