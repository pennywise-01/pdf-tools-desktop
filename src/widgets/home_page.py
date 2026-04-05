import sys
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QGridLayout, 
    QHBoxLayout, QFrame, QScrollArea, QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QFont, QColor

# Import feature tabs
from tabs.merge_tab import MergeTab
from tabs.split_tab import SplitTab
from tabs.compress_tab import CompressTab
from tabs.ocr_tab import OcrTab
from tabs.encrypt_tab import EncryptTab
from tabs.rotate_pages_tab import RotatePagesTab
from tabs.remove_pages_tab import RemovePagesTab
from tabs.extract_pages_tab import ExtractPagesTab
from tabs.images_to_pdf_tab import ImagesToPdfTab
from tabs.html_to_pdf_tab import HtmlToPdfTab
from tabs.pdf_to_images_tab import PdfToImagesTab
from tabs.watermark_tab import WatermarkTab
from tabs.scrub_metadata_tab import ScrubMetadataTab
from tabs.sign_pdf_tab import SignPdfTab
from tabs.redact_tab import RedactTab
from tabs.repair_tab import RepairTab
from tabs.shred_tab import ShredTab
from tabs.extract_text_tab import ExtractTextTab
from tabs.pdf_to_word_tab import PDFToWordTab
from tabs.pdf_to_excel_tab import PDFToExcelTab
from tabs.office_to_pdf_tab import OfficeToPDFTab
from tabs.pdf_to_pptx_tab import PDFToPPTXTab

# Color palette constants - Deep Ocean Theme
COLORS = {
    'bg': '#0a0f14',
    'surface': '#141c24',
    'surface_elevated': '#1a242e',
    'surface_hover': '#202d3a',
    'border': '#2a3744',
    'border_hover': '#3d4f5f',
    'text': '#f0f4f8',
    'text_secondary': '#94a3b8',
    'text_dim': '#64748b',
    'accent': '#38bdf8',
    'accent_hover': '#7dd3fc',
    'accent_muted': 'rgba(56, 189, 248, 0.15)',
    # Category colors
    'organize': '#3b82f6',
    'optimize': '#f59e0b',
    'convert_to': '#10b981',
    'convert_from': '#8b5cf6',
    'edit': '#ec4899',
    'security': '#ef4444',
}

CATEGORIES = [
    {
        "title": "Organize",
        "icon": "📁",
        "color": COLORS['organize'],
        "description": "Merge, split, and manage PDF pages",
        "items": [
            ("Merge PDF", MergeTab, "Combine multiple files into one"),
            ("Split PDF", SplitTab, "Divide PDF into separate files"),
            ("Remove Pages", RemovePagesTab, "Delete unwanted pages"),
            ("Extract Pages", ExtractPagesTab, "Save specific pages"),
        ]
    },
    {
        "title": "Optimize",
        "icon": "⚡",
        "color": COLORS['optimize'],
        "description": "Compress, repair, and enhance PDFs",
        "items": [
            ("Compress PDF", CompressTab, "Reduce file size"),
            ("OCR PDF", OcrTab, "Extract text from scanned documents"),
            ("Repair PDF", RepairTab, "Fix corrupted PDF files"),
        ]
    },
    {
        "title": "Convert to PDF",
        "icon": "📥",
        "color": COLORS['convert_to'],
        "description": "Create PDFs from various formats",
        "items": [
            ("Images to PDF", ImagesToPdfTab, "Convert JPG, PNG to PDF"),
            ("Word to PDF", OfficeToPDFTab, "Convert DOCX documents"),
            ("PowerPoint to PDF", OfficeToPDFTab, "Convert PPTX presentations"),
            ("Excel to PDF", OfficeToPDFTab, "Convert XLSX spreadsheets"),
            ("HTML to PDF", HtmlToPdfTab, "Convert web pages"),
        ]
    },
    {
        "title": "Convert from PDF",
        "icon": "📤",
        "color": COLORS['convert_from'],
        "description": "Export PDFs to other formats",
        "items": [
            ("PDF to Images", PdfToImagesTab, "Export as JPG or PNG"),
            ("PDF to Word", PDFToWordTab, "Convert to editable DOCX"),
            ("PDF to PowerPoint", PDFToPPTXTab, "Convert to PPTX slides"),
            ("PDF to Excel", PDFToExcelTab, "Extract to spreadsheet"),
            ("Extract Text", ExtractTextTab, "Export as plain text"),
        ]
    },
    {
        "title": "Edit",
        "icon": "✏️",
        "color": COLORS['edit'],
        "description": "Modify and annotate PDFs",
        "items": [
            ("Rotate Pages", RotatePagesTab, "Change page orientation"),
            ("Add Watermark", WatermarkTab, "Add text or image overlay"),
        ]
    },
    {
        "title": "Security",
        "icon": "🔒",
        "color": COLORS['security'],
        "description": "Protect and secure your documents",
        "items": [
            ("Encrypt PDF", EncryptTab, "Add password protection"),
            ("Redact PDF", RedactTab, "Permanently hide sensitive content"),
            ("Scrub Metadata", ScrubMetadataTab, "Remove hidden information"),
            ("Secure Shred", ShredTab, "Permanently delete files"),
            ("Sign PDF", SignPdfTab, "Add digital signature"),
        ]
    },
]

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class CollapsibleCategory(QWidget):
    """A collapsible category widget with expandable feature list"""
    
    def __init__(self, category_data, main_window, parent=None):
        super().__init__(parent)
        self.category = category_data
        self.main_window = main_window
        self.is_expanded = False
        self.setup_ui()
    
    def setup_ui(self):
        self.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Category header button
        self.header_btn = QPushButton()
        self.header_btn.setObjectName("categoryHeader")
        self.header_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        # Keep enough vertical room for both title + description on high-DPI displays.
        self.header_btn.setFixedHeight(88)
        self.header_btn.clicked.connect(self.toggle_expand)
        
        header_layout = QHBoxLayout(self.header_btn)
        header_layout.setContentsMargins(20, 16, 20, 16)
        header_layout.setSpacing(16)
        
        # Color indicator
        indicator = QFrame()
        indicator.setFixedSize(4, 48)
        indicator.setStyleSheet(f"background-color: {self.category['color']}; border-radius: 2px;")
        header_layout.addWidget(indicator)
        
        # Icon
        icon_label = QLabel(self.category["icon"])
        icon_label.setFixedWidth(52)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet(
            "background: transparent;"
            "font-family: 'Segoe UI Emoji', 'Apple Color Emoji', 'Noto Color Emoji';"
            "font-size: 26px;"
        )
        header_layout.addWidget(icon_label)
        
        # Title and description
        text_container = QWidget()
        text_container.setStyleSheet("background: transparent;")
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(4)
        
        title = QLabel(self.category["title"])
        title.setFont(QFont("Plus Jakarta Sans", 16, QFont.Weight.DemiBold))
        title.setStyleSheet(f"color: {COLORS['text']}; background: transparent;")
        
        desc = QLabel(self.category["description"])
        desc.setFont(QFont("Plus Jakarta Sans", 12))
        desc.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        
        text_layout.addWidget(title)
        text_layout.addWidget(desc)
        header_layout.addWidget(text_container, 1)
        
        # Tool count badge
        count_badge = QLabel(f"{len(self.category['items'])}")
        count_badge.setFont(QFont("Plus Jakarta Sans", 11, QFont.Weight.Medium))
        count_badge.setFixedSize(28, 28)
        count_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        count_badge.setStyleSheet(f"""
            color: {self.category['color']}; 
            background-color: {self.category['color']}20; 
            border-radius: 14px;
        """)
        header_layout.addWidget(count_badge)
        
        # Expand arrow
        self.arrow_label = QLabel("›")
        self.arrow_label.setFont(QFont("Plus Jakarta Sans", 20, QFont.Weight.Normal))
        self.arrow_label.setFixedWidth(24)
        self.arrow_label.setStyleSheet(f"color: {COLORS['text_dim']}; background: transparent;")
        header_layout.addWidget(self.arrow_label)
        
        # Header styling
        self.header_btn.setStyleSheet(f"""
            QPushButton#categoryHeader {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
                min-height: 88px;
                max-height: 88px;
                padding: 0px;
                text-align: left;
            }}
            QPushButton#categoryHeader:hover {{
                background-color: {COLORS['surface_elevated']};
                border-color: {self.category['color']}60;
            }}
        """)
        
        layout.addWidget(self.header_btn)
        
        # Expandable content container
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background: transparent;")
        self.content_widget.setVisible(False)
        
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 8, 0, 0)
        content_layout.setSpacing(8)
        
        # Feature buttons grid
        grid = QGridLayout()
        grid.setSpacing(10)
        grid.setContentsMargins(0, 0, 0, 0)
        
        for idx, item in enumerate(self.category["items"]):
            row = idx // 3
            col = idx % 3
            btn = self.create_feature_button(item)
            grid.addWidget(btn, row, col)
        
        # Fill empty columns
        items_in_last_row = len(self.category["items"]) % 3
        if items_in_last_row > 0:
            last_row = len(self.category["items"]) // 3
            for col in range(items_in_last_row, 3):
                spacer = QWidget()
                spacer.setStyleSheet("background: transparent;")
                grid.addWidget(spacer, last_row, col)
        
        content_layout.addLayout(grid)
        layout.addWidget(self.content_widget)
    
    def toggle_expand(self):
        self.is_expanded = not self.is_expanded
        self.content_widget.setVisible(self.is_expanded)
        
        # Update arrow direction
        self.arrow_label.setText("˅" if self.is_expanded else "›")
        
        # Update header style when expanded
        if self.is_expanded:
            self.header_btn.setStyleSheet(f"""
                QPushButton#categoryHeader {{
                    background-color: {self.category['color']}15;
                    border: 1px solid {self.category['color']}60;
                    border-radius: 12px;
                    min-height: 88px;
                    max-height: 88px;
                    padding: 0px;
                    text-align: left;
                }}
                QPushButton#categoryHeader:hover {{
                    background-color: {self.category['color']}20;
                    border-color: {self.category['color']};
                }}
            """)
        else:
            self.header_btn.setStyleSheet(f"""
                QPushButton#categoryHeader {{
                    background-color: {COLORS['surface']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 12px;
                    min-height: 88px;
                    max-height: 88px;
                    padding: 0px;
                    text-align: left;
                }}
                QPushButton#categoryHeader:hover {{
                    background-color: {COLORS['surface_elevated']};
                    border-color: {self.category['color']}60;
                }}
            """)
    
    def create_feature_button(self, item_data):
        """Create a feature button tile"""
        name, tab_class, description = item_data
        is_pro = bool(
            tab_class
            and hasattr(self.main_window, "is_widget_pro")
            and self.main_window.is_widget_pro(tab_class)
        )
        
        color = self.category['color']
        
        btn = QPushButton()
        btn.setObjectName("featureTile")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(84)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        tooltip = description
        if is_pro:
            tooltip = f"{description}\n\nPro feature: Requires activation"
        btn.setToolTip(tooltip)
        
        # Use a QWidget container inside button for proper label display
        container = QWidget(btn)
        container.setStyleSheet("background: transparent;")
        container.setGeometry(0, 0, 300, 84)
        
        btn_layout = QVBoxLayout(container)
        btn_layout.setContentsMargins(16, 14, 16, 14)
        btn_layout.setSpacing(4)
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(8)
        
        name_label = QLabel(name, container)
        name_label.setFont(QFont("Plus Jakarta Sans", 13, QFont.Weight.Medium))
        name_label.setStyleSheet(f"color: {COLORS['text']}; background: transparent;")
        name_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        top_row.addWidget(name_label)
        top_row.addStretch()

        if is_pro:
            pro_label = QLabel("PRO", container)
            pro_label.setFont(QFont("Plus Jakarta Sans", 9, QFont.Weight.Bold))
            pro_label.setStyleSheet(
                "color: #0a0f14; background-color: #f59e0b; "
                "border-radius: 6px; padding: 2px 6px;"
            )
            pro_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            top_row.addWidget(pro_label)
        
        desc_label = QLabel(description, container)
        desc_label.setFont(QFont("Plus Jakarta Sans", 11))
        desc_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        desc_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        
        btn_layout.addLayout(top_row)
        btn_layout.addWidget(desc_label)
        
        btn.setStyleSheet(f"""
            QPushButton#featureTile {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 10px;
                min-height: 84px;
                max-height: 84px;
                padding: 0px;
                text-align: left;
            }}
            QPushButton#featureTile:hover {{
                background-color: {color}15;
                border-color: {color}80;
            }}
            QPushButton#featureTile:pressed {{
                background-color: {color}25;
                border-color: {color};
            }}
        """)
        
        # Make container resize with button
        def resize_container(event):
            container.setGeometry(0, 0, btn.width(), btn.height())
        btn.resizeEvent = resize_container
        
        if tab_class:
            btn.clicked.connect(lambda: self.main_window.switch_to_feature_by_widget(tab_class))
        
        return btn


class HomePage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setup_ui()
    
    def setup_ui(self):
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("background-color: transparent;")
        
        container = QWidget()
        container.setStyleSheet(f"background-color: {COLORS['bg']};")
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(48, 40, 48, 40)
        main_layout.setSpacing(24)
        
        # Header
        header_widget = self.create_header()
        main_layout.addWidget(header_widget)
        
        # Categories
        for category in CATEGORIES:
            cat_widget = CollapsibleCategory(category, self.main_window)
            main_layout.addWidget(cat_widget)
        
        main_layout.addStretch()
        
        scroll_area.setWidget(container)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll_area)
    
    def create_header(self):
        """Create compact header"""
        header_widget = QWidget()
        header_widget.setStyleSheet("background: transparent;")
        header_layout = QVBoxLayout(header_widget)
        header_layout.setSpacing(8)
        header_layout.setContentsMargins(0, 0, 0, 16)
        
        # Title row
        title_row = QHBoxLayout()
        title_row.setSpacing(0)
        
        title_main = QLabel("PDF Tools")
        title_main.setFont(QFont("Plus Jakarta Sans", 28, QFont.Weight.Bold))
        title_main.setStyleSheet(f"color: {COLORS['text']}; background: transparent;")
        
        title_accent = QLabel(" Desktop")
        title_accent.setFont(QFont("Plus Jakarta Sans", 28, QFont.Weight.Bold))
        title_accent.setStyleSheet(f"color: {COLORS['accent']}; background: transparent;")
        
        title_row.addWidget(title_main)
        title_row.addWidget(title_accent)
        title_row.addStretch()
        
        subtitle = QLabel("Click a category below to see available tools")
        subtitle.setFont(QFont("Plus Jakarta Sans", 13))
        subtitle.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        
        header_layout.addLayout(title_row)
        header_layout.addWidget(subtitle)
        
        return header_widget
