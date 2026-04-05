import sys
import os
import subprocess

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

# Anti-Tampering Security Check (MVP 8)
# Must be done early before other imports
try:
    from utils.anti_tampering import initialize_security
except ImportError:
    try:
        from src.utils.anti_tampering import initialize_security
    except ImportError:
        from .utils.anti_tampering import initialize_security

# Run security checks (set to False during development, True for production builds)
# Set via environment variable: PDF_TOOLS_DEV_MODE=1 to skip checks
dev_mode = os.environ.get('PDF_TOOLS_DEV_MODE', '0') == '1'
pro_blocking_disabled = os.environ.get('PDF_TOOLS_DISABLE_PRO_BLOCK', '0') == '1'
if not dev_mode:
    initialize_security(exit_on_failure=True)
else:
    print("Security: Development mode - anti-tampering checks disabled.")

if pro_blocking_disabled:
    print("License: Development override enabled - Pro gating is bypassed.")

# Ensure imports like `from tabs...` and `from features...` work
# both in development (running `python src/main.py`) and in tests
# (importing `src.main`).
_SRC_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SRC_DIR)
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QComboBox, QToolBar,
    QStatusBar, QLabel, QWidget, QHBoxLayout, QFrame, QPushButton
)
from PyQt6.QtGui import QIcon, QFont, QPixmap, QPainter, QPen, QColor, QPolygon
from PyQt6.QtCore import QSize, Qt, QPoint

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
from widgets.home_page import HomePage
from widgets.license_dialog import open_activation_dialog, show_pro_feature_locked_dialog
from utils.license_manager import LicenseManager, is_pro_feature_name

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = _PROJECT_ROOT
    return os.path.join(base_path, relative_path)


def maybe_bootstrap_libreoffice():
    """
    Best-effort LibreOffice setup launcher for source runs.
    Returns True when bootstrap setup was launched.
    """
    if os.environ.get("PDF_TOOLS_AUTO_SETUP_LIBREOFFICE", "1") != "1":
        return False

    if sys.platform != "win32":
        return False

    try:
        from features.pdf_to_pptx import find_libreoffice
    except Exception:
        return False

    if find_libreoffice():
        return False

    setup_script = resource_path("setup_libreoffice.py")
    if not os.path.exists(setup_script):
        print("Setup: LibreOffice not found and setup script is unavailable.")
        return False

    try:
        creationflags = 0x08000000 if sys.platform == "win32" else 0
        subprocess.Popen([sys.executable, setup_script], creationflags=creationflags)
        print("Setup: LibreOffice not found. Started setup_libreoffice.py in background.")
        return True
    except Exception as exc:
        print(f"Setup: Failed to launch LibreOffice bootstrap: {exc}")
        return False

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Tools Desktop")
        self.setMinimumSize(1200, 800)
        self.pro_blocking_disabled = pro_blocking_disabled
        self.license_manager = LicenseManager()
        
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
        for feature in self.features:
            feature["pro"] = is_pro_feature_name(feature["name"])

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
        self.refresh_license_ui()
        self.switch_to_home()

    def setup_toolbar(self):
        self.toolbar = QToolBar("Main Toolbar")
        self.toolbar.setObjectName("featureToolbar")
        self.addToolBar(self.toolbar)
        self.toolbar.setMovable(False)
        self.toolbar.setFixedHeight(74)
        self.toolbar.setStyleSheet("""
            QToolBar {
                background-color: #0a1016;
                border: none;
                border-bottom: 1px solid #223241;
                spacing: 0px;
                padding: 0px;
            }
            QWidget#featureToolbarContainer {
                background: transparent;
                border: none;
            }
            QPushButton#featureHomeButton {
                min-width: 42px;
                max-width: 42px;
                min-height: 42px;
                max-height: 42px;
                background-color: rgba(56, 189, 248, 0.08);
                border: 1px solid rgba(56, 189, 248, 0.30);
                border-radius: 11px;
                padding: 0px;
            }
            QPushButton#featureHomeButton:hover {
                background-color: rgba(56, 189, 248, 0.18);
                border-color: rgba(125, 211, 252, 0.60);
            }
            QPushButton#featureHomeButton:pressed {
                background-color: rgba(14, 165, 233, 0.30);
                border-color: #38bdf8;
            }
            QFrame#featureToolbarSeparator {
                background-color: #304658;
                min-width: 1px;
                max-width: 1px;
                min-height: 30px;
                max-height: 30px;
            }
            QLabel#featureSelectorLabel {
                color: #8ea5b8;
                font-size: 12px;
                font-weight: 600;
                background: transparent;
            }
            QComboBox#featureSelector {
                background-color: #111923;
                color: #f0f4f8;
                border: 1px solid #2d4253;
                border-radius: 10px;
                padding: 8px 12px;
                padding-right: 30px;
                min-height: 22px;
                font-size: 13px;
                font-weight: 500;
            }
            QComboBox#featureSelector:hover {
                border-color: #3e5a6f;
                background-color: #152230;
            }
            QComboBox#featureSelector:focus {
                border-color: #38bdf8;
            }
            QComboBox#featureSelector::drop-down {
                border: none;
                width: 24px;
            }
            QComboBox#featureSelector::down-arrow {
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #97adc1;
            }
            QComboBox#featureSelector QAbstractItemView {
                background-color: #141c24;
                color: #f0f4f8;
                border: 1px solid #2a3744;
                selection-background-color: rgba(56, 189, 248, 0.18);
                selection-color: #7dd3fc;
            }
            QPushButton#licenseActionButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0ea5e9, stop:1 #38bdf8);
                color: #04131d;
                border: 1px solid rgba(125, 211, 252, 0.65);
                border-radius: 10px;
                padding: 8px 16px;
                min-height: 22px;
                font-weight: 700;
            }
            QPushButton#licenseActionButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #38bdf8, stop:1 #7dd3fc);
                border-color: #a5f3fc;
            }
            QPushButton#licenseActionButton:pressed {
                background-color: #0ea5e9;
                border-color: #38bdf8;
            }
            QPushButton#licenseActionButton:disabled {
                background: #1a242e;
                color: #64748b;
                border-color: #2a3744;
            }
        """)
        
        # Create a container widget for the toolbar content
        toolbar_container = QWidget()
        toolbar_container.setObjectName("featureToolbarContainer")
        toolbar_container.setFixedHeight(52)
        toolbar_layout = QHBoxLayout(toolbar_container)
        toolbar_layout.setContentsMargins(12, 8, 12, 8)
        toolbar_layout.setSpacing(12)
        
        # Home button with icon only
        home_btn = QPushButton()
        home_btn.setObjectName("featureHomeButton")
        home_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        home_btn.setFixedSize(42, 42)
        home_btn.setToolTip("Home")
        
        # Create home icon using QPainter
        home_pixmap = QPixmap(24, 24)
        home_pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(home_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor("#f0f4f8"))
        pen.setWidth(2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        roof = QPolygon([QPoint(12, 3), QPoint(3, 10), QPoint(21, 10)])
        painter.drawPolyline(roof)
        painter.drawRect(5, 10, 14, 11)
        painter.drawRect(10, 14, 4, 7)
        painter.end()
        
        home_btn.setIcon(QIcon(home_pixmap))
        home_btn.setIconSize(QSize(24, 24))
        home_btn.clicked.connect(self.switch_to_home)
        toolbar_layout.addWidget(home_btn)
        
        # Separator
        separator = QFrame()
        separator.setObjectName("featureToolbarSeparator")
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFixedSize(1, 30)
        toolbar_layout.addWidget(separator)
        
        # Feature selector label
        selector_label = QLabel("Feature:")
        selector_label.setObjectName("featureSelectorLabel")
        toolbar_layout.addWidget(selector_label)
        
        # Feature selector dropdown
        self.feature_selector = QComboBox()
        self.feature_selector.setObjectName("featureSelector")
        self.feature_selector.setMinimumWidth(260)
        self.feature_selector.setMaximumWidth(360)
        
        self.feature_selector.addItem("Select a feature...")
        for feature in self.features:
            label = f"{feature['name']} [Pro]" if feature.get("pro") else feature["name"]
            self.feature_selector.addItem(QIcon(feature["icon_path"]), label)
        
        self.feature_selector.model().item(0).setEnabled(False)
        self.feature_selector.currentIndexChanged.connect(self.switch_to_feature_by_index)
        toolbar_layout.addWidget(self.feature_selector)
        
        toolbar_layout.addStretch()

        self.activate_license_btn = QPushButton("Activate License")
        self.activate_license_btn.setObjectName("licenseActionButton")
        self.activate_license_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.activate_license_btn.setMinimumWidth(156)
        self.activate_license_btn.clicked.connect(self.open_license_activation_dialog)
        toolbar_layout.addWidget(self.activate_license_btn)
        
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

        self.license_status_label = QLabel("License: Free")
        self.license_status_label.setFont(QFont("Plus Jakarta Sans", 10))
        self.license_status_label.setStyleSheet("color: #f59e0b; padding: 4px 8px;")
        self.status_bar.addPermanentWidget(self.license_status_label)
        
        # Version label
        version_label = QLabel("v2.0")
        version_label.setFont(QFont("Plus Jakarta Sans", 10))
        version_label.setStyleSheet("color: #2dd4bf; padding: 4px 8px;")
        self.status_bar.addPermanentWidget(version_label)

    def update_status(self, message):
        """Update the status bar message"""
        self.status_label.setText(message)

    def get_feature_by_widget(self, widget_class):
        for feature in self.features:
            if feature["widget"] == widget_class:
                return feature
        return None

    def is_widget_pro(self, widget_class):
        feature = self.get_feature_by_widget(widget_class)
        return bool(feature and feature.get("pro"))

    def refresh_license_ui(self):
        if self.pro_blocking_disabled:
            self.license_status_label.setText("License: Dev Override")
            self.license_status_label.setStyleSheet("color: #38bdf8; padding: 4px 8px;")
            self.activate_license_btn.setText("Activate License (Optional)")
            return

        if self.license_manager.has_valid_pro_license():
            self.license_status_label.setText("License: Pro Active")
            self.license_status_label.setStyleSheet("color: #22c55e; padding: 4px 8px;")
            self.activate_license_btn.setText("Manage License")
            return

        self.license_status_label.setText("License: Free")
        self.license_status_label.setStyleSheet("color: #f59e0b; padding: 4px 8px;")
        self.activate_license_btn.setText("Activate License")

    def open_license_activation_dialog(self):
        was_activated = open_activation_dialog(self, self.license_manager)
        self.refresh_license_ui()
        if was_activated:
            self.update_status("Pro license activated")

    def _set_feature_selector_for_widget(self, widget_class):
        self.feature_selector.blockSignals(True)
        for i, feature in enumerate(self.features):
            if feature["widget"] == widget_class:
                self.feature_selector.setCurrentIndex(i + 1)
                break
        self.feature_selector.blockSignals(False)

    def _sync_feature_selector_with_current_widget(self):
        current_widget = self.stacked_widget.currentWidget()
        target_index = 0
        for i, feature in enumerate(self.features):
            if self.feature_widgets[feature["widget"]] == current_widget:
                target_index = i + 1
                break

        self.feature_selector.blockSignals(True)
        self.feature_selector.setCurrentIndex(target_index)
        self.feature_selector.blockSignals(False)

    def _ensure_feature_access(self, feature):
        if not feature.get("pro"):
            return True
        if self.pro_blocking_disabled:
            return True
        if self.license_manager.can_access_feature(feature["name"]):
            return True

        unlocked_now = show_pro_feature_locked_dialog(
            self,
            feature_name=feature["name"],
            license_manager=self.license_manager,
        )
        if not unlocked_now:
            self.license_manager.record_pro_gate_denied(feature["name"])
        self.refresh_license_ui()
        return unlocked_now

    def switch_to_feature_by_widget(self, widget_class):
        feature = self.get_feature_by_widget(widget_class)
        if feature is None:
            return False

        if not self._ensure_feature_access(feature):
            self.update_status(f"Locked: {feature['name']} requires Pro")
            self._sync_feature_selector_with_current_widget()
            return False

        widget_to_show = self.feature_widgets[widget_class]
        self.stacked_widget.setCurrentWidget(widget_to_show)
        self.toolbar.setVisible(True)
        
        # Update status
        suffix = " [Pro]" if feature.get("pro") else ""
        self.update_status(f"Active: {feature['name']}{suffix}")

        # Update combobox to current feature
        self._set_feature_selector_for_widget(widget_class)
        return True

    def switch_to_feature_by_index(self, index):
        if index > 0:
            feature = self.features[index - 1]
            switched = self.switch_to_feature_by_widget(feature["widget"])
            if not switched:
                self._sync_feature_selector_with_current_widget()

    def switch_to_home(self):
        self.stacked_widget.setCurrentWidget(self.home_page)
        self.toolbar.setVisible(False)
        self._sync_feature_selector_with_current_widget()
        self.update_status("Welcome to PDF Tools Desktop")

if __name__ == "__main__":
    maybe_bootstrap_libreoffice()

    app = QApplication(sys.argv)
    
    # Load and apply stylesheet
    qss_path = resource_path("src/style.qss")
    try:
        with open(qss_path, "r") as f:
            qss = f.read()
        app.setStyleSheet(qss)
    except Exception as e:
        print(f"Warning: Could not load stylesheet: {e}")
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
