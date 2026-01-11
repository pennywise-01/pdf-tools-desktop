from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel
)
from widgets.pdf_preview import PdfPreviewWidget
from utils.error_handler import show_error_dialog

class FeatureTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setAcceptDrops(True)
        
        main_layout = QHBoxLayout(self)

        self.preview = PdfPreviewWidget()
        main_layout.addWidget(self.preview, 2)

        self.controls_layout = QVBoxLayout()
        main_layout.addLayout(self.controls_layout, 1)
        
        self.setup_controls()

    def show_error(self, message, detail=None, prefix="GEN"):
        show_error_dialog(self, message, detail, prefix)

    def setup_controls(self):
        # This method should be overridden by subclasses
        pass
        
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
            
    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            self.handle_file_drop(files)
            
    def handle_file_drop(self, files):
        # This method should be overridden by subclasses
        pass