import sys
import os

# Install Network Lock (Security Feature)
# Must be done before other imports that might initialize networking.
try:
    from network_security import install_network_lock
except ImportError:
    # If running as part of a package (e.g. tests), try relative or package import
    try:
        from src.network_security import install_network_lock
    except ImportError:
        # Last resort: relative import if __package__ is set
        from .network_security import install_network_lock

install_network_lock()

# Ensure imports like `from tabs...` and `from features...` work
# both in development (running `python src/main.py`) and in tests
# (importing `src.main`).
_SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QComboBox, QToolBar,
)
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QSize

from tabs.merge_tab import MergeTab
from tabs.split_tab import SplitTab
from tabs.remove_pages_tab import RemovePagesTab
from tabs.encrypt_tab import EncryptTab
from tabs.rotate_pages_tab import RotatePagesTab
from tabs.extract_pages_tab import ExtractPagesTab
from tabs.scrub_metadata_tab import ScrubMetadataTab
from tabs.images_to_pdf_tab import ImagesToPdfTab
from tabs.html_to_pdf_tab import HtmlToPdfTab
from tabs.pdf_to_images_tab import PdfToImagesTab
from tabs.sign_pdf_tab import SignPdfTab
from tabs.watermark_tab import WatermarkTab
from tabs.compress_tab import CompressTab
from tabs.redact_tab import RedactTab
from tabs.shred_tab import ShredTab
from tabs.repair_tab import RepairTab
from tabs.ocr_tab import OcrTab
from tabs.extract_text_tab import ExtractTextTab
from tabs.pdf_to_word_tab import PDFToWordTab
from tabs.pdf_to_excel_tab import PDFToExcelTab
from tabs.office_to_pdf_tab import OfficeToPDFTab
from tabs.pdf_to_pptx_tab import PDFToPPTXTab
from tabs.ocr_tab import OcrTab
from widgets.home_page import HomePage

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Tools Desktop")
        self.setMinimumSize(800, 600)

        self.features = [
            {"name": "Merge", "icon_path": resource_path("icon/merge-removebg-preview.png"), "widget": MergeTab},
            {"name": "Split", "icon_path": resource_path("icon/split-removebg-preview.png"), "widget": SplitTab},
            {"name": "Remove Pages", "icon_path": resource_path("icon/remove-removebg-preview.png"), "widget": RemovePagesTab},
            {"name": "Encrypt", "icon_path": resource_path("icon/encrypt-removebg-preview.png"), "widget": EncryptTab},
            {"name": "Rotate Pages", "icon_path": resource_path("icon/rotate-removebg-preview.png"), "widget": RotatePagesTab},
            {"name": "Extract Pages", "icon_path": resource_path("icon/extract-removebg-preview.png"), "widget": ExtractPagesTab},
            {"name": "Scrub Metadata", "icon_path": resource_path("icon/metadata-removebg-preview.png"), "widget": ScrubMetadataTab},
            {"name": "Images to PDF", "icon_path": resource_path("icon/png-removebg-preview.png"), "widget": ImagesToPdfTab},
            {"name": "HTML to PDF", "icon_path": resource_path("icon/html-removebg-preview.png"), "widget": HtmlToPdfTab},
            {"name": "PDF to Images", "icon_path": resource_path("icon/png.png"), "widget": PdfToImagesTab},
            {"name": "Sign PDF", "icon_path": resource_path("icon/encrypt-removebg-preview.png"), "widget": SignPdfTab},
            {"name": "Watermark", "icon_path": resource_path("icon/pdf-app-icon.png"), "widget": WatermarkTab},
            {"name": "Compress", "icon_path": resource_path("icon/remove-removebg-preview.png"), "widget": CompressTab},
            {"name": "Redact", "icon_path": resource_path("icon/remove-removebg-preview.png"), "widget": RedactTab},
            {"name": "Secure Shred", "icon_path": resource_path("icon/remove-removebg-preview.png"), "widget": ShredTab},
            {"name": "Repair PDF", "icon_path": resource_path("icon/merge-removebg-preview.png"), "widget": RepairTab},
            {"name": "OCR (Text)", "icon_path": resource_path("icon/png-removebg-preview.png"), "widget": OcrTab},
            {"name": "Extract Text", "icon_path": resource_path("icon/pdf-app-icon.png"), "widget": ExtractTextTab},
            {"name": "PDF to Word", "icon_path": resource_path("icon/pdf-app-icon.png"), "widget": PDFToWordTab},
            {"name": "PDF to Excel", "icon_path": resource_path("icon/pdf-app-icon.png"), "widget": PDFToExcelTab},
            {"name": "Office to PDF", "icon_path": resource_path("icon/pdf-app-icon.png"), "widget": OfficeToPDFTab},
            {"name": "PDF to PPTX", "icon_path": resource_path("icon/ppttopdf.png"), "widget": PDFToPPTXTab},
        ]

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.home_page = HomePage(self)
        self.stacked_widget.addWidget(self.home_page)

        self.feature_widgets = {}
        for feature in self.features:
            widget_class = feature["widget"]
            widget_instance = widget_class()
            self.stacked_widget.addWidget(widget_instance)
            self.feature_widgets[widget_class] = widget_instance

        self.setup_toolbar()
        self.switch_to_home()

    def setup_toolbar(self):
        self.toolbar = QToolBar("Main Toolbar")
        self.addToolBar(self.toolbar)
        self.toolbar.setMovable(False)

        home_action = QAction(QIcon(resource_path("icon/pdf-app-icon.png")), "Home", self)
        home_action.triggered.connect(self.switch_to_home)
        self.toolbar.addAction(home_action)

        self.feature_selector = QComboBox()
        self.feature_selector.setIconSize(QSize(24, 24))
        self.feature_selector.addItem("Select a feature")
        for feature in self.features:
            self.feature_selector.addItem(QIcon(feature["icon_path"]), feature["name"])
        
        self.feature_selector.model().item(0).setEnabled(False)
        self.feature_selector.currentIndexChanged.connect(self.switch_to_feature_by_index)
        self.toolbar.addWidget(self.feature_selector)

    def switch_to_feature_by_widget(self, widget_class):
        # Block signals to prevent recursive loop
        self.feature_selector.blockSignals(True)
        
        widget_to_show = self.feature_widgets[widget_class]
        self.stacked_widget.setCurrentWidget(widget_to_show)
        self.toolbar.setVisible(True)

        # Update combobox to current feature
        for i, feature in enumerate(self.features):
            if feature["widget"] == widget_class:
                self.feature_selector.setCurrentIndex(i + 1)
                break
        
        # Unblock signals
        self.feature_selector.blockSignals(False)

    def switch_to_feature_by_index(self, index):
        if index > 0:
            feature = self.features[index - 1]
            self.switch_to_feature_by_widget(feature["widget"])

    def switch_to_home(self):
        self.stacked_widget.setCurrentWidget(self.home_page)
        self.toolbar.setVisible(False)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    with open(resource_path("src/style.qss"), "r") as f:
        qss = f.read()

    dropdown_arrow_path = resource_path("icon/dropdown-removebg-preview.png").replace("\\", "/")
    qss = qss.replace("{DROPDOWN_ARROW}", dropdown_arrow_path)
    app.setStyleSheet(qss)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())