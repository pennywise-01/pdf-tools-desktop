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
    QStatusBar, QLabel, QWidget, QHBoxLayout, QFrame, QPushButton
)
from PyQt6.QtGui import QIcon, QAction, QFont, QPixmap, QImage
from PyQt6.QtCore import QSize, Qt

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
        self.setMinimumSize(1200, 800)
        
        # Set application icon
        app_icon_path = resource_path("icon/pdf-app-icon.png")
        if os.path.exists(app_icon_path):
            self.setWindowIcon(QIcon(app_icon_path))

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
        self.setup_status_bar()
        self.switch_to_home()

    def setup_toolbar(self):
        self.toolbar = QToolBar("Main Toolbar")
        self.addToolBar(self.toolbar)
        self.toolbar.setMovable(False)
        self.toolbar.setFixedHeight(56)
        
        # Create a container widget for the toolbar content
        toolbar_container = QWidget()
        toolbar_container.setStyleSheet("background: transparent;")
        toolbar_layout = QHBoxLayout(toolbar_container)
        toolbar_layout.setContentsMargins(16, 0, 16, 0)
        toolbar_layout.setSpacing(16)
        
        # Home button with icon only
        home_btn = QPushButton()
        home_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        home_btn.setFixedSize(44, 44)
        home_btn.setToolTip("Home")
        home_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 10px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: rgba(56, 189, 248, 0.15);
                border: 1px solid rgba(56, 189, 248, 0.3);
            }
            QPushButton:pressed {
                background-color: rgba(56, 189, 248, 0.25);
            }
        """)
        
        # Create home icon using SVG
        home_icon_svg = """
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f0f4f8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
            <polyline points="9 22 9 12 15 12 15 22"></polyline>
        </svg>
        """
        home_icon = QIcon(QPixmap.fromImage(QImage.fromData(home_icon_svg.encode())))
        home_btn.setIcon(home_icon)
        home_btn.setIconSize(QSize(24, 24))
        
        # Connect button click
        home_btn.clicked.connect(self.switch_to_home)
        
        toolbar_layout.addWidget(home_btn)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setStyleSheet("background-color: #30363d;")
        separator.setFixedWidth(1)
        separator.setFixedHeight(28)
        toolbar_layout.addWidget(separator)
        
        # Feature selector label
        selector_label = QLabel("Feature:")
        selector_label.setFont(QFont("Plus Jakarta Sans", 12))
        selector_label.setStyleSheet("color: #8b949e; background: transparent;")
        toolbar_layout.addWidget(selector_label)
        
        # Feature selector dropdown
        self.feature_selector = QComboBox()
        self.feature_selector.setIconSize(QSize(20, 20))
        self.feature_selector.setMinimumWidth(260)
        self.feature_selector.setMaximumWidth(360)
        self.feature_selector.setFont(QFont("Plus Jakarta Sans", 12))
        self.feature_selector.setStyleSheet("""
            QComboBox {
                background-color: #262d36;
                color: #e6edf3;
                border: 1px solid #30363d;
                border-radius: 8px;
                padding: 8px 14px;
                padding-right: 36px;
            }
            QComboBox:hover {
                border-color: #484f58;
                background-color: #30363d;
            }
            QComboBox:focus {
                border-color: #2dd4bf;
            }
            QComboBox::drop-down {
                border: none;
                width: 28px;
            }
            QComboBox::down-arrow {
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #8b949e;
                width: 0px;
                height: 0px;
            }
            QComboBox QAbstractItemView {
                background-color: #1c2128;
                color: #e6edf3;
                border: 1px solid #30363d;
                border-radius: 8px;
                selection-background-color: rgba(45, 212, 191, 0.15);
                selection-color: #2dd4bf;
                padding: 6px;
                outline: none;
            }
        """)
        
        self.feature_selector.addItem("Select a feature...")
        for feature in self.features:
            self.feature_selector.addItem(QIcon(feature["icon_path"]), feature["name"])
        
        self.feature_selector.model().item(0).setEnabled(False)
        self.feature_selector.currentIndexChanged.connect(self.switch_to_feature_by_index)
        toolbar_layout.addWidget(self.feature_selector)
        
        toolbar_layout.addStretch()
        
        # Add the container to toolbar
        self.toolbar.addWidget(toolbar_container)

    def setup_status_bar(self):
        """Setup the status bar with Industrial Utility styling"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setFont(QFont("Plus Jakarta Sans", 11))
        self.status_label.setStyleSheet("color: #8b949e; padding: 4px 8px;")
        self.status_bar.addWidget(self.status_label)
        
        # Version label
        version_label = QLabel("v2.0")
        version_label.setFont(QFont("Plus Jakarta Sans", 10))
        version_label.setStyleSheet("color: #2dd4bf; padding: 4px 8px;")
        self.status_bar.addPermanentWidget(version_label)

    def update_status(self, message):
        """Update the status bar message"""
        self.status_label.setText(message)

    def switch_to_feature_by_widget(self, widget_class):
        # Block signals to prevent recursive loop
        self.feature_selector.blockSignals(True)
        
        widget_to_show = self.feature_widgets[widget_class]
        self.stacked_widget.setCurrentWidget(widget_to_show)
        self.toolbar.setVisible(True)
        
        # Update status
        for feature in self.features:
            if feature["widget"] == widget_class:
                self.update_status(f"Active: {feature['name']}")
                break

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
        self.update_status("Welcome to PDF Tools Desktop")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Load and apply stylesheet
    try:
        with open(resource_path("src/style.qss"), "r") as f:
            qss = f.read()
        app.setStyleSheet(qss)
    except Exception as e:
        print(f"Warning: Could not load stylesheet: {e}")
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
