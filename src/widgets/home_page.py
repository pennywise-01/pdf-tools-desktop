import sys
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QGridLayout, QHBoxLayout
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon

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

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class HomePage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)
        
        # Grid layout for columns
        grid_layout = QGridLayout()
        grid_layout.setSpacing(20)
        # Make columns stretch equally
        for i in range(6):
            grid_layout.setColumnStretch(i, 1)
            
        main_layout.addLayout(grid_layout)

        # Define columns and their items
        # Structure: (Header, [ (ButtonText, TabClass, IconPath) ])
        columns = [
            ("Organized PDF", [
                ("Merge PDF", MergeTab, "icon/merge-removebg-preview.png"),
                ("Split PDF", SplitTab, "icon/split-removebg-preview.png"),
                ("Remove Pages", RemovePagesTab, "icon/remove-removebg-preview.png"),
                ("Extract Pages", ExtractPagesTab, "icon/extract-removebg-preview.png"),
            ]),
            ("Optimized PDF", [
                ("Compress PDF", CompressTab, "icon/pdf-app-icon.png"),
                ("OCR PDF", OcrTab, "icon/pdf-app-icon.png"),
                ("Repair PDF", RepairTab, "icon/merge-removebg-preview.png"),
            ]),
            ("Convert to PDF", [
                ("JPG to PDF", ImagesToPdfTab, "icon/png-removebg-preview.png"),
                ("Word to PDF", OfficeToPDFTab, "icon/wordtopdf.png"), 
                ("PPTX to PDF", OfficeToPDFTab, "icon/ppttopdf.png"),
                ("Excel to PDF", OfficeToPDFTab, "icon/pdf-app-icon.png"),
                ("HTML to PDF", HtmlToPdfTab, "icon/html-removebg-preview.png"),
            ]),
             ("Convert from PDF", [
                ("PDF to JPG", PdfToImagesTab, "icon/png.png"),
                ("PDF to Word", PDFToWordTab, "icon/wordtopdf.png"), 
                ("PDF to PPTX", PDFToPPTXTab, "icon/ppttopdf.png"),
                ("PDF to Excel", PDFToExcelTab, "icon/pdf-app-icon.png"),
                ("Extract Text", ExtractTextTab, "icon/pdf-app-icon.png"),
            ]),
             ("Edit PDF", [
                ("Rotate PDF", RotatePagesTab, "icon/rotate-removebg-preview.png"),
                ("Add Watermark", WatermarkTab, "icon/pdf-app-icon.png"),
            ]),
            ("PDF Security", [
                ("Encrypt PDF", EncryptTab, "icon/encrypt-removebg-preview.png"),
                ("Redact PDF", RedactTab, "icon/pdf-app-icon.png"),
                ("Scrub PDF", ScrubMetadataTab, "icon/metadata-removebg-preview.png"),
                ("Secure Shred", ShredTab, "icon/pdf-app-icon.png"),
                ("Sign PDF", SignPdfTab, "icon/encrypt-removebg-preview.png"),
            ]),
        ]

        # Create columns
        for col_idx, (header_text, items) in enumerate(columns):
            # Header
            header = QLabel(header_text)
            header.setStyleSheet("""
                font-size: 14px; 
                font-weight: bold; 
                color: #333333; 
                padding: 10px; 
                border: 1px solid #333;
                background-color: white;
            """)
            header.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header.setFixedHeight(45)
            grid_layout.addWidget(header, 0, col_idx)
            
            # Items
            for row_idx, (name, tab, icon_path) in enumerate(items):
                btn = self.create_button(name, tab, icon_path)
                grid_layout.addWidget(btn, row_idx + 1, col_idx)
            
            # Add stretch at the end of each column? No, grid handles it.
            # But if columns have different lengths, the grid naturally handles alignment.
            # If we want them top-aligned, we should align items.
            grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        main_layout.addStretch()

    def create_button(self, name, tab_class, icon_path):
        btn = QPushButton(name)
        btn.setFixedHeight(45)
        
        # Set Icon
        if icon_path:
             full_path = resource_path(icon_path)
             if os.path.exists(full_path):
                 btn.setIcon(QIcon(full_path))
                 btn.setIconSize(QSize(20, 20))
        
        # Style
        # Dark text color #222222
        btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding-left: 15px;
                color: #222222;
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e5e5e5;
                border-color: #bbb;
            }
            QPushButton:disabled {
                color: #888;
                background-color: #f9f9f9;
            }
        """)
        
        if tab_class:
            btn.clicked.connect(lambda: self.main_window.switch_to_feature_by_widget(tab_class))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            btn.setEnabled(False)
            btn.setToolTip("Coming Soon")
            
        return btn
