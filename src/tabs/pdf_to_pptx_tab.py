from PyQt6.QtWidgets import QMessageBox, QFileDialog, QProgressDialog, QLabel, QPushButton
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont
from widgets.feature_tab import FeatureTab, COLORS
from features.pdf_to_pptx import convert_pdf_to_pptx

class PDFToPPTXWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, input_path, output_path, enable_pdftoppt=False):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.enable_pdftoppt = enable_pdftoppt

    def run(self):
        try:
            success, msg = convert_pdf_to_pptx(
                self.input_path,
                self.output_path,
                enable_pdftoppt=self.enable_pdftoppt,
            )
            if success:
                self.finished.emit(msg)
            else:
                self.error.emit(msg)
        except Exception as e:
            self.error.emit(str(e))

class PDFToPPTXTab(FeatureTab):
    def __init__(self, parent=None):
        # FeatureTab.__init__ calls setup_controls(), so initialize these first
        # and do not overwrite them afterwards.
        self.selected_file = None
        self.mode_label = None
        self.experimental_pdftoppt_checkbox = None
        super().__init__(parent)

    def setup_controls(self):
        # Header
        header = self.create_header(
            "PDF to PowerPoint",
            "Convert PDF pages into editable PowerPoint slides (extracts text and images)."
        )
        self.controls_layout.addWidget(header)

        # File selection
        self.file_container, self.file_label = self.create_file_label()
        self.controls_layout.addWidget(self.file_container)

        select_button = self.create_secondary_button("Select PDF", self.select_file)
        self.controls_layout.addWidget(select_button)

        self.experimental_pdftoppt_checkbox = self.create_checkbox(
            "Use experimental editable engine (pdftoppt)",
            checked=False,
        )
        self.experimental_pdftoppt_checkbox.setToolTip(
            "When enabled, tries pdftoppt before standard fallback engines. "
            "If warning volume is too high, it is automatically skipped."
        )
        self.controls_layout.addWidget(self.experimental_pdftoppt_checkbox)

        # Action button
        self.action_button = self.create_primary_button("Convert to PPTX", self.run_action)
        self.controls_layout.addWidget(self.action_button)

        # Result mode indicator
        self.mode_label = QLabel()
        self.mode_label.setWordWrap(True)
        self._set_mode_label(
            "Output mode: Waiting to run conversion",
            COLORS['text_secondary'],
            COLORS['surface_elevated']
        )
        self.controls_layout.addWidget(self.mode_label)
        
        self.controls_layout.addStretch()

    def _set_mode_label(self, text, text_color, bg_color):
        if not self.mode_label:
            return

        self.mode_label.setText(text)
        self.mode_label.setStyleSheet(
            f"""
            QLabel {{
                color: {text_color};
                background-color: {bg_color};
                border: 1px solid {COLORS['border']};
                border-radius: 10px;
                padding: 10px 12px;
                font-size: 12px;
            }}
            """
        )

    def _update_mode_from_message(self, message):
        lower_msg = (message or "").lower()

        if "pdftoppt" in lower_msg and "warning count exceeded" in lower_msg:
            self._set_mode_label(
                "Output mode: Fallback after experimental engine warnings",
                COLORS['warning'],
                COLORS['surface_elevated']
            )
            return

        if "pdftoppt" in lower_msg:
            self._set_mode_label(
                "Output mode: Experimental editable engine",
                COLORS['accent'],
                COLORS['surface_elevated']
            )
            return

        if "image-based slides" in lower_msg or "high-quality images" in lower_msg:
            self._set_mode_label(
                "Output mode: Visual fallback (text is not editable)",
                COLORS['warning'],
                COLORS['surface_elevated']
            )
            return

        if "scanned" in lower_msg and "non-editable" in lower_msg:
            self._set_mode_label(
                "Output mode: Editable best effort (scanned source may still limit editability)",
                COLORS['warning'],
                COLORS['surface_elevated']
            )
            return

        self._set_mode_label(
            "Output mode: Editable best effort",
            COLORS['success'],
            COLORS['surface_elevated']
        )

    def select_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select PDF", "", "PDF Files (*.pdf)")
        if file:
            self.selected_file = file
            filename = file.split('/')[-1].split('\\')[-1]
            self.file_label.setText(filename)
            self.preview.load_pdf(file)
            self._set_mode_label(
                "Output mode: Waiting to run conversion",
                COLORS['text_secondary'],
                COLORS['surface_elevated']
            )

    def run_action(self):
        if not self.selected_file:
            QMessageBox.warning(self, "No File Selected", "Please select a PDF file.")
            return

        output_path, _ = QFileDialog.getSaveFileName(self, "Save PowerPoint", "", "PowerPoint Files (*.pptx)")
        if output_path:
            enable_pdftoppt = bool(
                self.experimental_pdftoppt_checkbox and self.experimental_pdftoppt_checkbox.isChecked()
            )
            self._set_mode_label(
                (
                    "Output mode: Converting (experimental engine enabled)"
                    if enable_pdftoppt
                    else "Output mode: Converting (auto-selecting best engine)"
                ),
                COLORS['accent'],
                COLORS['surface_elevated']
            )
            self.progress_dialog = QProgressDialog("Converting to PowerPoint...", "Cancel", 0, 0, self)
            self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            self.progress_dialog.show()

            self.worker = PDFToPPTXWorker(
                self.selected_file,
                output_path,
                enable_pdftoppt=enable_pdftoppt,
            )
            self.worker.finished.connect(self.on_finished)
            self.worker.error.connect(self.on_error)
            self.worker.start()
            self.action_button.setEnabled(False)

    def on_finished(self, msg):
        self.progress_dialog.close()
        self._update_mode_from_message(msg)
        QMessageBox.information(self, "Success", msg)
        self.action_button.setEnabled(True)

    def on_error(self, error_message):
        self.progress_dialog.close()
        self._set_mode_label(
            "Output mode: Conversion failed",
            COLORS['error'],
            COLORS['surface_elevated']
        )
        self.show_error("An error occurred.", error_message, "P2P")
        self.action_button.setEnabled(True)

    def handle_file_drop(self, files):
        if files:
            file = files[0]
            if file.lower().endswith('.pdf'):
                self.selected_file = file
                filename = file.split('/')[-1].split('\\')[-1]
                self.file_label.setText(filename)
                self.preview.load_pdf(file)
                self._set_mode_label(
                    "Output mode: Waiting to run conversion",
                    COLORS['text_secondary'],
                    COLORS['surface_elevated']
                )
